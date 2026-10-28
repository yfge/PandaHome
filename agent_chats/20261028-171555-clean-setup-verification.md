## Summary

Independently verify the shared setup changes with Python 3.13.5 in a new virtual environment without system site-packages, using a fixed temporary API source snapshot. The final snapshot suite passed: **369 passed, 4 skipped**, with configuration parsing, password hashing/verification, TestClient requests, and dependency checks also passing.

Installation on this host required a process-local selection of an existing compatible macOS SDK. The default host SDK/linker combination failed even for a minimal standalone C program; this is not evidence that the default installation command works on this machine.

## Changes

- Added this verification log; this verification session did not change production source or stage/commit files.
- Verified the earlier documentation review in `agent_chats/20261028-165335-shared-setup-review.md`: `README.md`, `README.zh.md`, `AGENTS.md`, and `CLAUDE.md` specify one `api/` working directory for migration/bootstrap/API commands, the frontend in a second repository-root terminal, Next.js 16, and the actual hook dependencies. Root separately clarified `docs/auth-lifecycle.md` using the same working-directory convention.
- Verified root's `api/.env.example` correction to `AUTH_HASHING_SCHEMES=["bcrypt"]` with `Settings(_env_file=...)`.
- After independent failure reproduction, root updated `api/pyproject.toml` to require `bcrypt>=4.0.1,<5` and `pydantic[email]>=2.4.0`; its test extras also declare `httpx>=0.27.0`. Only this authorized manifest refresh was copied into the isolated source snapshot.
- The relay agent made two test-only compatibility fixes. `api/tests/test_upnp_gateway.py` explicitly saves/restores the State-backed service in `try/finally`, while `api/tests/test_relay.py` constructs a temporary fake checkout for its checkout-boundary assertion. Only those two authorized test files were refreshed before the final run. No production behavior changed for these test fixes, and pytest was not pinned to an older version.

## Outcome

The updated manifest installs into the isolated environment when this host uses its existing compatible SDK for the build process. The final tests passed with newer resolved dependencies than the developer interpreter, rather than relying on packages already installed globally.

The snapshot excluded `.env`, databases, logs, virtual environments, Git metadata, and caches. It retained `.env.example`. All package installation and tests subsequently used that snapshot; root's concurrent commits did not change the test source. Application configuration inherited from the host was removed from the verification subprocess environment, and imports were checked to resolve to the snapshot or its own virtual environment.

No production database was migrated or moved, no real administrator was bootstrapped, no public API/server was started, and no router mappings or deployment settings were changed. In-process API tests, loopback test doubles, and read-only host interface queries are distinct from production or physical-router acceptance.

## Verification

### Installation and negative cases

1. Created a Python 3.13.5 venv with `include-system-site-packages = false` and attempted `python -m pip install -e '<snapshot>/api[test]'`.
2. The default build failed for `netifaces==0.11.0`. Its configure checks reported no supported networking functions, followed by `netifaces.c:210:6: error: You need to add code for your platform.`
3. Retrying with temporary `-Wno-error=implicit-function-declaration -Wno-error=implicit-int` did not fix the failure. A minimal `/usr/bin/clang` compile/link independently failed against SDK 27.0 with `libSystem.B.tbd: unknown architecture arm64e.x1-macos`; no system/SDK configuration was changed.
4. Independently installing the remaining declared dependencies exposed the missing `email-validator` runtime dependency: importing the project's `UserBase`/authentication code failed because it uses Pydantic `EmailStr`.
5. After a supplementary email-validator installation, the project's `get_password_hash('setup-probe-password')` failed with bcrypt 5.0.0 and Passlib 1.7.4: `ValueError: password cannot be longer than 72 bytes`. The application supplied a short password; Passlib's backend self-test triggered the incompatible bcrypt behavior. The default bcrypt algorithm was not replaced.
6. After refreshing the authorized manifest fixes, the full editable installation passed with only the child process's `SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk`. No CFLAGS were required. This run built the official netifaces source distribution into a wheel and installed it into the isolated venv.

The relay agent independently confirmed the default SDK failure and the compatible-SDK build from the unmodified official netifaces source distribution. Conditional SDK selection is a host toolchain workaround, not a project runtime change or an unconditional clean-install success claim.

### Positive checks

- `Settings(_env_file='<snapshot>/api/.env.example')`: passed; the hashing-scheme list parses and `DATABASE_URL` remains exactly `sqlite:///./app.db`.
- Project `get_password_hash` and `verify_password`: passed for the correct password and rejected an incorrect password with bcrypt 4.3.0 / Passlib 1.7.4.
- `httpx`/FastAPI `TestClient` import and an actual in-process request: passed.
- `netifaces.interfaces()` and `netifaces.gateways()`: passed as read-only host queries; the imported extension resides in this venv.
- `python -m pip check`: passed, `No broken requirements found.`
- Initial complete snapshot pytest run: 352 passed, 4 skipped, 1 failed, 16 errors. The failures isolated test portability: pytest 9.2's MonkeyPatch old-value handling does not preserve Starlette State's custom storage, and a checkout-boundary test assumed real `.git` metadata despite the deliberate source-snapshot exclusion.
- After only the two authorized test refreshes: `python -m pytest tests -q --tb=short -rs` from the snapshot's `api/` directory: **369 passed, 4 skipped, 45 warnings in 26.84 seconds**, exit 0.
- All four skips are optional native frp integration cases requiring `PANDAHOME_FRP_BIN_DIR`. This isolated run does not claim native frp acceptance; any separately reported developer-environment native tests remain a separate proof layer.
- Remaining warnings concern Starlette's future httpx transition and aiohttp BasicAuth/auth deprecations; they did not fail this run.

### Observed dependency versions

| Package | Existing developer interpreter | Isolated verification venv |
| --- | --- | --- |
| Python | 3.13.5 | 3.13.5 |
| bcrypt | 4.0.1 | 4.3.0 |
| Passlib | 1.7.4 | 1.7.4 |
| Pydantic | 2.10.3 | 2.14.1 |
| pydantic-settings | 2.5.2 | 2.16.2 |
| email-validator | 2.2.0 | 2.3.0 |
| FastAPI | 0.115.6 | 0.162.0 |
| Starlette | 0.41.3 | 1.10.0 |
| httpx | 0.27.2 | 0.28.1 |
| pytest | 8.3.3 | 9.2.0 |
| pytest-asyncio | 0.24.0 | 1.4.1 |
| SQLAlchemy | 2.0.36 | 2.1.6 |
| async-upnp-client | 0.45.0 | 0.49.0 |
| netifaces | 0.11.0 | 0.11.0 |

### Reproducible evidence

The fixed snapshot and venv are under `/var/folders/rc/ffg_cryd6jsbjc2srvhbqnc40000gn/T/pandahome-clean-setup-bxfp7j6e/`. Sanitized durable evidence is under `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/setup-clean-env-20261028/`; the independent native build investigation is beside it in `setup-toolchain-20261028/`.

The evidence contains sanitized pip logs, bcrypt before/after reports, the first and final pytest outputs, base/fresh version reports, a verified artifact SHA256 manifest, and `source-sha256.json` covering 81 source/config/test files. Private package-index URLs were removed from captured pip output; application `.env` files, credentials, binaries, and databases were not copied into the evidence bundle.

Final refreshed source hashes:

- `api/pyproject.toml`: `53b135046f2e1dd6a76340bde115c482a47a0d30c2ae32d9d5db2a5d1967fbfb`
- `api/.env.example`: `99e7a86ea9c834c3514799aa67865b14870a029514ab006e0580dd0cd5e1031f`
- `api/tests/test_upnp_gateway.py`: `3f8da0f5f571d3ddcb56a62a0f07c8ce5a3efcb500fda190c9be43c3c5429f33`
- `api/tests/test_relay.py`: `da47c528755e419a98e65e4eab36c8a108c1b4ae7752ec3ef32eb1f4ddc3af57`

## Next steps

- Root agent owns staging and atomic delivery of the authorized setup, documentation, dependency, and test compatibility changes, including this log.
- Retain the documented distinction between the host-specific compatible-SDK installation and an unmodified default toolchain. Do not switch the system SDK or replace the networking library as part of this verification.
- Preserve the existing relative SQLite URL and same-`api/` working-directory instructions. Production migrations, deployment, physical-router reachability, and native frp acceptance were not performed by this clean-environment check.
