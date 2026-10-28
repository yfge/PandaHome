# Backend Runtime Dependency Audit

Initial audit: 2025-10-29. Setup verification refreshed: 2026-10-28.

## Method
- Reviewed `api/src/app` modules for third-party imports involved in UPnP control, authentication, and Aliyun DNS orchestration.
- Matched imported libraries against the dependency list declared in `api/pyproject.toml`.

## Findings

### Covered dependencies
The following imports already have matching entries in `api/pyproject.toml`:
- `fastapi`, `uvicorn`
- `sqlalchemy`
- `pydantic[email]`, `pydantic-settings` (the email extra supplies the `EmailStr` validator)
- `python-dotenv`
- `miniupnpc`
- `aliyun-python-sdk-core`, `aliyun-python-sdk-alidns`

### Runtime requirements now declared
| Package requirement | Imported from | Purpose | Notes |
| --- | --- | --- | --- |
| `async-upnp-client>=0.37.0` | `async_upnp_client.client_factory`, `async_upnp_client.aiohttp`, `async_upnp_client.search` | Async UPnP discovery and SOAP control used by `UPNPService`. | Required for runtime UPnP operations. |
| `aiohttp>=3.9.0` | Transitive dependency for `AiohttpSessionRequester`. | HTTP transport underpinning async UPnP requests. | Explicit requirement avoids relying on optional extra resolution. |
| `netifaces>=0.11.0` | `import netifaces` | Enumerates gateways and interfaces for UPnP discovery. | Needed for cross-platform network introspection. |
| `python-jose[cryptography]>=3.3.0` | `from jose import JWTError, jwt` | JWT encoding/decoding in authentication helpers. | Include `[cryptography]` extra for HS256/RS256 support. |
| `passlib[bcrypt]>=1.7.4` | `from passlib.context import CryptContext` | Password hashing/verification for users. | `[bcrypt]` extra pulls in secure hash backend. |
| `bcrypt>=4.0.1,<5` | Required by `passlib`'s bcrypt scheme. | Provides the actual bcrypt implementation for hashing passwords. | Passlib 1.7.4's backend self-test is incompatible with bcrypt 5's over-72-byte rejection; preserve the existing hashing scheme with a compatible 4.x backend. |
| `python-multipart>=0.0.6` | `OAuth2PasswordRequestForm` (FastAPI) | Enables FastAPI to parse form-encoded login payloads. | Mandatory for `/token` form submission handling. |

### Test and configuration requirements

- Install `api[test]` for pytest/pytest-asyncio and `httpx`, used by FastAPI's
  TestClient. Runtime-only FastAPI does not guarantee that test dependency.
- `pydantic[email]` is required by the existing user models' `EmailStr` fields.
- Keep bcrypt below 5 while using Passlib 1.7.4: its backend self-test fails even
  for a short application password with bcrypt 5's new length rejection. The
  existing bcrypt hashing scheme and stored-password format are unchanged.
- `.env` list values use JSON, for example `AUTH_HASHING_SCHEMES='["bcrypt"]'`.
  The shipped environment example is validated directly with Pydantic Settings.

### macOS native build note

`netifaces` remains required by UPnP interface/gateway discovery. On the validated
macOS arm64/Python 3.13 host, the default SDK 27 selection failed even a minimal
C link: its `libSystem.B.tbd` contained an architecture unsupported by the
installed linker. A working SDK was already installed; selecting it for only
the package-install process built netifaces 0.11.0 and its interface/gateway
calls worked. No library replacement, compiler flags or system SDK changes were
needed.

If the same diagnostic occurs and this compatible SDK exists on the machine,
run the installation from the repository root in the activated virtual environment:

```bash
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk python -m pip install -e "api[test]"
```

The SDK path is host-specific; use an installed SDK compatible with the selected
compiler/linker. This process environment override does not switch the system's
developer directory or change application defaults. The ordinary installation
command remains appropriate when the selected native toolchain works.
