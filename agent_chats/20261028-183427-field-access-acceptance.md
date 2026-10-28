## Summary

Start real field acceptance under `field-20261028-183427Z` for public application
access, physical-router ingress and P2P traversal across separate networks. The
new user authorization replaces standby-only limits while preserving closed UI
findings and the accepted `d19968e`/product `4efe286` baseline. Access owns real
API/nonce application evidence, the resource ledger and shared delivery; PM only
coordinates and reviews independently.

## Changes

- `tasks.md`: add three explicitly unpassed field acceptance tasks.
- `docs/field-acceptance-20261028.md`: acceptance distinctions, owner/resource
  coordination and this run's external evidence directory.
- `agent_chats/20261028-183427-field-access-acceptance.md`: current field-session
  evidence and blockers; previous UE/UI and DNS logs remain untouched.
- Created external `run-context.json`, `source-sha256.json` and an initially empty
  `resources.json`. Provisional per-owner high-port ranges coordinate ownership;
  they do not assert availability or authorize taking an existing resource.

## Outcome

The genuine isolated API completed login, unchanged network detection, disabled
service create/update/check/delete and local nonce readiness. It observed real
UPnP availability with different VPN observer and physical WAN addresses. The
fresh test database has zero service rows and both owned listeners are closed.
No Access DNS or router write occurred. Public application and direct P2P remain
unpassed. UPnP private-candidate ingress evidence is recorded separately, pending
committed-source/default-path and native ownership checks.

The minimal direct WAN target fix was independently reviewed, regression-tested
and committed as `65dc3a8` with normal hooks. It changes neither conservative auto
selection nor mapping ownership or external verification requirements. P2P owns
the ECS temporary relay lifecycle. Access reserves 58110–58139, UPnP owns TCP58471
and UDP58472, P2P reserves 58310–58339; existing rules and processes are preserved.

## Verification

- Read-only initial `git status --short`: clean; HEAD `d19968e`.
- Inspected current project instructions, task board and deployment/Access source
  references. Earlier localhost/frp and DNS results remain separate proof layers.
- Created source hashes from current tracked API/web/script files; external
  bundle path is recorded in the field document.
- Delegated independent live local deployment/configuration preflight, project
  topology source review and actual-API/nonce harness preparation. They do not
  write shared source or stage/commit.
- Real API phase: `api-harness/api_nonce_candidate.py --execute --ttl 300 --mode direct --local-ip <physical-LAN> --public-port 58111` using existing Conda Python; exit0. Evidence: `api-harness/20261028-192447Z-eac195/evidence.jsonl`, 19:24:47–19:25:18 UTC. No detector/network mock and no publication; cleanup independently confirmed.
- Direct WAN source fix: 199 related backend tests, Ruff and actual commit hooks passed. See `agent_chats/20261028-192108-direct-wan-candidate.md` for expected red/green regressions. Earlier 373 backend /103 frontend and full build remain historical baseline evidence, not a claim of field connectivity.

## Next steps

Report actual configuration locations, suitable existing hosts/roles, current
topology, independently measurable entrances and specific missing capabilities.
Then execute supported real end-to-end paths and retain failed/unavailable paths
as such. Use an isolated test DB/admin/API if needed; never expose management
APIs publicly, change existing credentials/mappings or repurpose unknown hosts.
No coding, scripting, documentation or commit is delegated to PM.
