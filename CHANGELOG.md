# Changelog

## 1.0.0 — 2026-11-19
- Added conservative OOXML metadata-only engine, atomic output, fail-closed format handling, ZIP checks and macro SHA-256 comparisons.
- Added CLI, CircleCI test config, regression tests and explicit security limitations.

## 2.0.0a1 — 2026-11-19
- Add read-only OOXML risk inventory for PII indicators, VBA presence, embedded parts, hidden markers, revisions and external references.
- Expose `--audit` via CLI and six new regression tests.
- 12 tests passed in locally assembled v1+v2 code; hosted CI and Office application compatibility remain unverified.
- Not a certified sanitizer for confidential or classified document release.

## 2.0.0a2 — 2026-11-19
- Add independent, read-only package verification with macro/content hashes, package relationship checks, and explicit incomplete/failed status.
- Refuse existing output and digitally signed packages to avoid destructive replacement and signature invalidation.
- Add seven regression tests; 19 total passed locally with Python 3.13. CI and real Office application checks are not yet verified.

## 3.0.0a1 — 2026-11-19
- Add fail-closed guarded workflow: preflight heuristic audit, metadata-only cleanup, independent package verification and postflight scan.
- Block macro-containing, embedded-object, comment, tracked-change, hidden-content, external-link, and detected PII indicator documents in guarded mode.
- Add `--guarded` CLI and five regression tests, bringing locally executed suite to 24 tests.
- Not a content redactor or classification clearance tool; hosted CI and Office app compatibility not verified.
- Harden default reports with filename indexes and opaque package-part IDs; 25 local regression tests passed.

## 3.0.0a2 — 2026-11-19
- Apply shared hostile-ZIP checks to sanitizer, audit, and output verifier.
- Reject path traversal, symlinks, encrypted/unsupported members; flag signatures in audits.
- Hide macro member paths in default reports and suppress exception detail leaks.
- Preserve default OPC XML namespaces to fix a real-world LibreOffice opening failure.
- Add seven regression tests (32 local tests passed, Python 3.13); successful one-DOCX LibreOffice 25.2 rendering and content comparison.
- Hosted CI, Microsoft Office and full format compatibility remain unverified.

## 3.0.0a3 — 2026-11-19
- Verify temporary sanitized packages independently before they become visible at the destination.
- Reject concurrent destination creation with non-overwriting hard-link publication.
- Reject oversized XML parts and aggregate XML payloads.
- Add seven regression/integration tests: 39 tests passed locally (Python 3.13).
- Generated Word, Excel, and PowerPoint samples reopened via their Python Office libraries and converted successfully to PDF by LibreOffice.
- Hosted CircleCI, Microsoft Office compatibility, full-content redaction, VBA source sanitization, and signed installers remain unverified.


## 3.0.0a4 — 2026-11-20
- Scrub ZIP archive comment, per-member comments, ZIP extra fields and per-member timestamps from sanitized copies.
- Independently verify cleaned ZIP members have no residual container metadata.
- Flag archive metadata and potentially sensitive member filenames without disclosing detected values in default reports.
- Replace raw removed-part names with counts in public cleanup reports.
- Let guarded processing clean removable ZIP metadata while blocking non-removable indicators.
- Add five regression tests (44/44 passed locally on assembled source); three LibreOffice conversion smoke tests passed.
- Hosted CI, Microsoft Office testing, full content redaction, VBA source sanitization, and installable stable release remain outstanding.


## 3.0.0a5 — 2026-11-21
- Improve heuristic detection of sensitive strings split across Office XML text runs.
- Flag potential confidentiality/classification marking text for **human review**, including text split across XML elements.
- Keep extracted values and classification marking text out of default reports.
- Add five regression tests for split email addresses, guarded blocking, review markings and private-value-safe reports.
- Locally assembled source: 49/49 regression tests passed with Python. Hosted CI on the exact new commit and Microsoft Office compatibility are separate release gates.


## 4.0.0b1 — 2026-11-21
- Added offline Tkinter desktop GUI with file/folder selection, default audit mode, guarded metadata-copy mode, and privacy-safe JSON report export.
- Added reusable batch orchestration with deterministic file ordering, symlink avoidance, and filename-collision rejection.
- Added Python wheel packaging and GUI entry point; native signed installers remain out of scope.
- Maintained conservative metadata-only semantics; no claims of classified-data clearance, VBA source cleaning, or universal Office support.


## 4.1.0b1 — 2026-11-22
- Add review-only exposure inventory for hidden Office content, external data connections, cached data, custom XML and embedded controls.
- Keep guarded mode fail-closed on these findings; never remove them automatically.
- Add six synthetic Excel, Word and PowerPoint regression tests, totaling 62 tests passed locally on the assembled source.
- Built an installable Python wheel. Hosted CircleCI and real Office application testing remain distinct verification requirements.


## 4.2.0b1 — XFCE desktop and verified update checks
- XFCE Office menu launcher, scalable icon and automatic per-login update check, rate-limited once daily.
- GUI **Check updates** button and `office-sanitizer-update` CLI.
- Check official GitHub Release metadata and require a matching Debian package with SHA-256 asset digest.
- Authenticated user-confirmed APT installation; no silent root update.
- Add 12 updater regression tests. Local source: 76/76 tests passed; Debian extraction, CLI and GUI smoke tests passed.
- Pending: publish a GitHub Release asset or signed APT repository to supply future upgrades.
