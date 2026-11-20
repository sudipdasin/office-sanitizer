# Office Sanitizer v3.0.0a4 source verification

Date: 2026-11-20

Status: **source pre-release, not a certified sanitization or classification-clearance product**.

- Locally assembled source package: Python 3.13 `python -m pytest -q` — **44 passed**; `python -m compileall -q office_sanitizer tests` — passed.
- Generated DOCX/XLSX/PPTX samples passed metadata cleanup and independent verification, reopened using python-docx/openpyxl/python-pptx, and successfully converted to nonempty PDF documents using local LibreOffice.
- Five additional tests cover ZIP archive/member comments, extra fields, timestamps, filenames with PII indicators and report privacy.
- **Provenance caveat:** prior v3.0.0a3 local archive differed from the GitHub starting-tree blobs, so these local tests are not proof that the precise GitHub commit passed CI.
- Hosted CircleCI, real Microsoft Office tests, broad legacy format support, full-body redaction, VBA source cleaning and signed installable releases remain unverified/unimplemented.
- Source files must not be treated as safe to share solely because package verification passes.

Release blockers: https://github.com/sudipdasin/office-sanitizer/issues/1
