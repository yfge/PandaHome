"""Private, atomic configuration storage outside the source checkout."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from pydantic import SecretStr

from ..schemas.relay import RelayProfile
from .relay import FrpRelay, RelayConfig
from .relay_ssh import RelaySSHConfig


class RelayProfileError(RuntimeError):
    """Safe configuration error with no path, credential or input disclosure."""


class RelayProfileStore:
    def __init__(self, state_dir: Path, defaults: RelayProfile):
        self.directory = Path(state_dir).expanduser().resolve()
        self.path = self.directory / "relay-profile.json"
        self.defaults = defaults
        for parent in Path(__file__).resolve().parents:
            if (parent / ".git").exists() and self.directory.is_relative_to(parent):
                raise RelayProfileError("Relay configuration must be outside the source checkout")

    def load(self) -> tuple[RelayProfile, str]:
        try:
            # Missing is the only fallback. Malformed/inaccessible managed data
            # must not silently redirect an existing service to env defaults.
            if not self.path.exists() and not self.path.is_symlink():
                return self.defaults, "environment"
            if self.path.is_symlink() or self.path.stat().st_uid != os.getuid():
                raise OSError
            if self.path.stat().st_mode & 0o077:
                raise OSError
            profile = RelayProfile.model_validate(json.loads(self.path.read_text()))
            return profile, "managed"
        except (OSError, ValueError):
            raise RelayProfileError("Unable to read private relay configuration") from None

    @staticmethod
    def with_credentials(incoming: RelayProfile, current: RelayProfile) -> RelayProfile:
        token = incoming.token if incoming.token is not None else current.token
        if incoming.clear_token:
            token = SecretStr("")
        return incoming.model_copy(update={"token": token, "clear_token": False})

    @contextmanager
    def prepare(self, profile: RelayProfile):
        temporary = None
        try:
            if self.directory.is_symlink():
                raise OSError
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.directory.stat().st_uid != os.getuid():
                raise OSError
            self.directory.chmod(0o700)
            fd, temporary = tempfile.mkstemp(prefix=".relay-profile-", dir=self.directory)
            payload = profile.model_dump(exclude={"token", "clear_token"})
            payload["token"] = profile.token.get_secret_value() if profile.token else ""
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump(payload, stream, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            yield lambda: os.replace(temporary, self.path)
        except OSError:
            raise RelayProfileError("Unable to save private relay configuration") from None
        finally:
            if temporary:
                Path(temporary).unlink(missing_ok=True)


def environment_profile(settings) -> RelayProfile:
    names = RelayProfile.model_fields.keys() - {"token", "clear_token"}
    return RelayProfile(**{
        name: getattr(settings, f"RELAY_{name.upper()}") for name in names
    }, token=settings.RELAY_TOKEN)


def profile_relay(state_dir: Path, profile: RelayProfile) -> FrpRelay:
    ssh = RelaySSHConfig(**{
        name: getattr(profile, f"ssh_{name}") for name in RelaySSHConfig.__dataclass_fields__
    }) if profile.ssh_enabled else None
    return FrpRelay(RelayConfig(
        state_dir=state_dir, server_addr=profile.server_addr, server_port=profile.server_port,
        public_host=profile.public_host, binary=profile.binary,
        token=profile.token.get_secret_value() if profile.token else "",
        tls_trusted_ca_file=profile.tls_trusted_ca_file, tls_server_name=profile.tls_server_name, ssh=ssh,
    ))
