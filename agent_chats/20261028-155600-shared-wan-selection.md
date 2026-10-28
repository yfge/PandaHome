## Summary

Reuse the now-delivered gateway service selector for automatic public-access detection.

## Changes

- `api/src/app/services/upnp.py`: remove the duplicate recursive WANIPConnection:1-only selector and delegate to the shared gateway helper.
- `api/tests/test_network_detection.py`: cover automatic WANIPConnection:2 and WANPPPConnection:1 compatibility.

## Outcome

Automatic detection and explicit gateway management share one supported-service policy. Existing method names remain compatible; unsupported devices return no service. Depends on the independently delivered gateway commit.

## Verification

- Mandatory isolated snapshot pre-commit hooks run Python lint and full API regression; no skips.
- No physical router mapping or network configuration changes were performed.

## Next steps

Complete final Feature 07 acceptance record; deployed network validation remains separate.
