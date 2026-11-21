# Office Sanitizer 4.1.0b1 — release validation

Date: 2026-11-22

- Python local source assembly: **62/62 tests passed**, including six synthetic Office exposure cases.
- `python -m compileall -q office_sanitizer tests` passed.
- Built a pure-Python wheel with pip using the local source assembly.
- These are local results: they are not evidence that the exact GitHub commit was executed in CircleCI. Hosted statuses must be checked separately.
- No claim of comprehensive personal/classified information removal, Office-version compatibility, VBA source cleaning, signed native distribution, or security certification.
- Community remains GPLv3; Pro-only source must remain private and respect license obligations.

Release gate: https://github.com/sudipdasin/office-sanitizer/issues/1
