# Backend Runtime Dependency Audit (2025-10-29)

## Method
- Reviewed `api/src/app` modules for third-party imports involved in UPnP control, authentication, and Aliyun DNS orchestration.
- Matched imported libraries against the dependency list declared in `api/pyproject.toml`.

## Findings

### Covered dependencies
The following imports already have matching entries in `api/pyproject.toml`:
- `fastapi`, `uvicorn`
- `sqlalchemy`
- `pydantic`, `pydantic-settings`
- `python-dotenv`
- `miniupnpc`
- `aliyun-python-sdk-core`, `aliyun-python-sdk-alidns`

### Missing runtime dependencies
| Package requirement | Imported from | Purpose | Notes |
| --- | --- | --- | --- |
| `async-upnp-client>=0.37.0` | `async_upnp_client.client_factory`, `async_upnp_client.aiohttp`, `async_upnp_client.search` | Async UPnP discovery and SOAP control used by `UPNPService`. | Required for runtime UPnP operations. |
| `aiohttp>=3.9.0` | Transitive dependency for `AiohttpSessionRequester`. | HTTP transport underpinning async UPnP requests. | Explicit pin avoids relying on optional extra resolution. |
| `netifaces>=0.11.0` | `import netifaces` | Enumerates gateways and interfaces for UPnP discovery. | Needed for cross-platform network introspection. |
| `python-jose[cryptography]>=3.3.0` | `from jose import JWTError, jwt` | JWT encoding/decoding in authentication helpers. | Include `[cryptography]` extra for HS256/RS256 support. |
| `passlib[bcrypt]>=1.7.4` | `from passlib.context import CryptContext` | Password hashing/verification for users. | `[bcrypt]` extra pulls in secure hash backend. |
| `bcrypt>=4.0.1` | Required by `passlib`'s bcrypt scheme. | Provides the actual bcrypt implementation for hashing passwords. | Keep explicit to ensure availability in runtime images. |
| `python-multipart>=0.0.6` | `OAuth2PasswordRequestForm` (FastAPI) | Enables FastAPI to parse form-encoded login payloads. | Mandatory for `/token` form submission handling. |

## Next actions
- Update `api/pyproject.toml` to include the missing requirements before packaging or deploying the backend.
- Re-run `uv pip install -e api` after updating dependencies to verify resolver success. (Tracked in Feature 01 – Step 2.)
