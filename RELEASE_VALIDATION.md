# Office Sanitizer v3.0.0a5 verification

Date: 2026-11-21

- Locally assembled Alpha 5 archive: **49/49 Python tests passed**; `python -m compileall -q office_sanitizer tests` passed.
- Five new tests exercise XML run-spanning indicators, guarded blocking and confidentiality-marking privacy.
- Note that prior source-archive and GitHub baseline trees differ; **local archive tests are not proof that the precise GitHub HEAD passed hosted CI**.
- Host CircleCI must report a passing build on this exact commit before it is declared CI validated.
- Actual Microsoft Office multi-version compatibility, full VBA source sanitization, content redaction and a signed installable stable release remain outstanding.
- This product is not certified for disclosure/declassification of confidential or classified information; outputs still require review.

Release blockers: https://github.com/sudipdasin/office-sanitizer/issues/1
