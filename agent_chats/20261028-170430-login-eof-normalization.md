## Summary

Deliver the coordinator's pure login-client EOF normalization as an independent
formatting commit so final all-files hooks require no source corrections.

## Changes

- `web/src/app/login/login-client.tsx`: remove one extra blank line at EOF.
- This record accompanies the exact formatting-only source change.

## Outcome

Bytes before the trailing CR/LF sequence are identical. Login behavior, layout,
credentials and authentication logic are unchanged.

## Verification

- Independent byte comparison of HEAD and working content excluding final CR/LF:
  equal; final newlines change from two to one.
- `git diff --check`: passed. Applicable mandatory commit hooks run without bypass.

## Next steps

This owner completes the remaining shared setup/docs delivery and final all-files
checks. No implementation follow-up is required for this normalization.
