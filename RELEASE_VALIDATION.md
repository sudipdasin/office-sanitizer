# Office Sanitizer v4.0.0b1 — verification record

Date: 2026-11-21

## Verified locally

- Source: prior v3.0.0a5 assembled archive plus v4 batch/desktop changes. Prior archives are not guaranteed byte-for-byte identical to GitHub's initial source tree; GitHub is the authoritative public source.
- Python 3.13: compileall passed; pytest: **56 passed**.
- Built an installable `py3-none-any` Python wheel with pip.
- Installed the wheel in a clean local Python virtual environment. `office-sanitizer --help` and `import office_sanitizer.gui` succeeded.
- The `office-sanitizer-gui` entry point launched under virtual X11 (`xvfb-run`) and remained open until controlled timeout, with no startup errors. This is only a GUI startup smoke test, not comprehensive UX certification.
- Earlier LibreOffice interoperability smoke tests covered generated DOCX/XLSX/PPTX files; no actual Microsoft Office environment was tested for v4.

## Open release gates

- Hosted CircleCI on exact v4 Community and private Pro commits must report passing statuses.
- No signed native Windows, macOS, RPM or DEB installer is distributed.
- Complete content redaction, VBA source sanitization, OLE legacy formats, advanced classification policy and broad Microsoft Office compatibility are not implemented.
- No classification clearance; all outputs require authorized human review.

Tracked at https://github.com/sudipdasin/office-sanitizer/issues/1
