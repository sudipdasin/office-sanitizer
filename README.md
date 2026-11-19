# Office Sanitizer Community v2.0.0 alpha 1

Conservative, offline, **metadata-only** sanitization for unencrypted OOXML Office files. Supported `.docx .docm .dotx .dotm .xlsx .xlsm .xltx .xltm .pptx .pptm .potx .potm .ppsx .ppsm`. VBA binaries are preserved byte-for-byte; macro source and embedded sensitive data are **not cleaned**.

**Not certified for classified information or unrestricted safe sharing.** The tool does not remove document body text, comments, hidden content, embedded objects or classification markings. Unsupported and legacy formats fail closed.

```bash
python -m pip install -e .
python -m office_sanitizer -o ./sanitized example.docm
python -m pytest -q
```

Output statuses say `metadata_cleaned_content_unreviewed`; this means only selected metadata was removed. CircleCI config in `.circleci/config.yml`; connect the repository in CircleCI to run it.

## v2 risk inspection (alpha)

```bash
python -m office_sanitizer --audit document.docm
python -m office_sanitizer -o ./sanitized document.docm
```

`--audit` is read-only, emits counts and package part names (not extracted sensitive values), and fails closed on corrupt or unexpectedly large packages. It flags VBA, embedded parts, collaboration, hidden content, tracked changes, external relationships, email addresses, and candidate AWS access keys. **It is a heuristic risk inventory, not a forensic or complete content scanner.** Text split across XML elements, images, legacy/OLE, encrypted or non-OOXML formats, and secrets hidden in VBA binary streams may not be detected. No scan result certifies safe sharing.

Run `python -m pytest -q` before deploying. This is a pre-release and must not be used as a classified document declassification tool.

## v2.0.0 alpha 2: independent package verification
Metadata-only cleaning remains narrow; it does not redact document content or VBA source.
The sanitizer now refuses to overwrite existing outputs or modify digitally signed OOXML packages.
Use `python -m office_sanitizer example.docm --verify-output sanitized/example.docm` to compare original and output part hashes and package relationships independently. A positive result means **package integrity only**, not confidentiality clearance. Open real documents in Office and review their content separately.

## v3.0.0 alpha 1 — guarded workflow (pre-release)

```bash
python -m office_sanitizer --guarded -o ./review-copies document.docx
```

Guarded mode performs a read-only preflight, blocks detected risks other than removable `docProps` metadata, writes a **metadata-only** copy when permitted, independently compares package contents, and rescans the output. A successful result is **`metadata_only_copy_requires_human_review`**, never cleared or safe to share. Macro-enabled files with VBA project binaries are blocked by guarded mode; the existing non-guarded metadata-only mode can preserve those binaries but cannot sanitize their source. Blocked files are not cleaned and originals are unchanged.

**Known limitations:** This does not redact classified content, names, arbitrary PII, scanned images, VBA code, unrecognized embedded objects, or all metadata. This is not suitable for unreviewed release of sensitive documents. The risk scanner is heuristic; absence of findings is not clearance. Real Microsoft Office/LibreOffice compatibility is not yet validated.
