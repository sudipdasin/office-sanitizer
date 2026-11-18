# Office Sanitizer Community v1.0.0

Conservative, offline, **metadata-only** sanitization for unencrypted OOXML Office files. Supported `.docx .docm .dotx .dotm .xlsx .xlsm .xltx .xltm .pptx .pptm .potx .potm .ppsx .ppsm`. VBA binaries are preserved byte-for-byte; macro source and embedded sensitive data are **not cleaned**.

**Not certified for classified information or unrestricted safe sharing.** The tool does not remove document body text, comments, hidden content, embedded objects or classification markings. Unsupported and legacy formats fail closed.

```bash
python -m pip install -e .
python -m office_sanitizer -o ./sanitized example.docm
python -m pytest -q
```

Output statuses say `metadata_cleaned_content_unreviewed`; this means only selected metadata was removed. CircleCI config in `.circleci/config.yml`; connect the repository in CircleCI to run it.
