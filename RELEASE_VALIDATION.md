# v3.0.0a2 verification record (2026-11-19)

Status: **source pre-release only; NOT safe-sharing certification**.

Local verification on Python 3.13: 32/32 regression tests and bytecode compilation passed. A generated DOCX processed through guarded mode passed independent package integrity checks. The sanitized document rendered in LibreOffice 25.2.3.2 after correction of OPC default namespace serialization; extracted PDF text matched that of the original document.

Community changes synchronized into private Pro; nine corresponding source/configuration/docs files had matching GitHub blob SHA values.

GitHub returned **no hosted CI status checks** for latest commits. A hosted CircleCI pass has not been verified. Microsoft Office and broader legacy/macro-enabled compatibility have not been validated. No signed installer, stable release, or GitHub release asset has been published.

No VBA source redaction, full document-content sanitization, classified document clearance, or authorization for document disclosure is implied. All outputs require human review.

Release blockers tracked in [issue #1](https://github.com/sudipdasin/office-sanitizer/issues/1).
