# v3.0.0a3 local verification — 2026-11-19

**Status: alpha source, not a certified sensitive/classified-data sanitizer.**

- Python 3.13: `python -m compileall -q office_sanitizer tests` passed.
- Python 3.13: `python -m pytest -q`: **39 passed** locally with python-docx, openpyxl and python-pptx.
- Generated DOCX/XLSX/PPTX samples sanitized, independently package-verified, reopened using each Office-format Python library and converted into nonempty PDFs by LibreOffice (exit status 0).
- New adversarial tests cover independent verification failure, destination-creation race and oversized XML.
- Hosted CircleCI and actual Microsoft Office compatibility are not verified. No signed installer or stable GitHub Release has been produced.
- VBA source is preserved rather than sanitized. No complete content redaction or classification clearance is implied; all outputs require human review.

Track release blockers in [issue #1](https://github.com/sudipdasin/office-sanitizer/issues/1).
