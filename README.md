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

Default audit reports now use file indexes and hashed package-part identifiers rather than potentially sensitive filenames.

## v3.0.0 alpha 2 — hardened source snapshot

The pre-release now rejects malicious ZIP paths, symlinks, unsupported/encrypted ZIP members and signed packages rather than attempting unsafe rewriting. Audits flag signed packages for review. Default reports conceal macro archive filenames. OOXML relationships and content-type manifests retain their original default namespace, fixing a LibreOffice interoperability failure.

**Verification scope:** 32 tests and bytecode compilation passed in the locally assembled Python 3.13 project. One generated DOCX was cleaned in guarded mode, independently package-verified and rendered by LibreOffice 25.2; rendered text matched the original. This smoke test does not imply support for all Office versions, confidential redaction, VBA sanitization or safe document distribution. No hosted CircleCI run or Microsoft Office test is claimed.

## 3.0.0 alpha 3: fail-closed publication and cross-format smoke tests

The metadata-only cleaner independently validates the temporary sanitized package before publishing it and uses non-overwriting hard-link creation. Excessive XML members are rejected. These safeguards **do not remove sensitive document body content, VBA source, hidden content or classification markings**. No scan or output certifies a document for release.

New tests include real generated Word (`python-docx`), Excel (`openpyxl`), and PowerPoint (`python-pptx`) document round trips. Install `pytest python-docx openpyxl python-pptx` and run `python -m pytest -q`. One local LibreOffice smoke run also rendered the cleaned files as PDFs; Microsoft Office and broader compatibility remain unverified. Hosted CircleCI execution must be checked separately.


## v3.0.0 Alpha 4 — ZIP-container privacy hardening

Office documents are ZIP containers. In addition to selected OOXML `docProps` parts, the metadata-only cleaner now rebuilds ZIP entries without original entry timestamps, comments, or extra fields, and omits the archive comment. ZIP member contents, including VBA project binaries, are preserved unchanged as verified by the independent checker. The scanner inventories those container fields and flags sensitive email indicators in package filenames without publishing matched values or archive member names.

Guarded mode permits removal of **container metadata** and selected document-property metadata, but blocks non-removable privacy indicators and VBA-containing documents. Source files are never overwritten. **Document body content, filenames referenced inside the OOXML package, VBA source, embedded payloads and classification markings are not sanitized.** No result constitutes clearance to distribute sensitive or classified material.

Local verification: 44 Python tests passed on an assembled source package; generated Word, Excel and PowerPoint samples converted to PDFs with LibreOffice. Hosted CI and Microsoft Office compatibility are not verified. The earlier v3.0.0a3 ZIP baseline differs from GitHub's initial tree and local tests must not be treated as a hosted validation of repository commits.


## v3.0.0 Alpha 5 — split-run risk detection

The read-only `--audit` scan now concatenates XML character-data runs within each package part before checking for email addresses, possible secrets and classification-marking *candidates*. This helps catch sensitive strings split by common Office formatting. Attributes remain scanned separately; output reports contain counts and opaque package identifiers, never matched text. Guarded mode blocks documents when these indicators are found.

This is a **heuristic indicator scan**, not comprehensive sensitive-data removal or official determination of classification. It cannot detect all secrets, text in images/binary objects, or cross-package fragments. Metadata-only cleaning and VBA binary preservation remain unchanged. Human review and relevant clearance procedures are required before disclosure.


## v4.0.0 Beta 1 — Offline desktop application

Start the desktop interface with `office-sanitizer-gui` (or `python -m office_sanitizer.gui`). Tkinter must be installed with your Python distribution (on Debian/Ubuntu: `python3-tk`). Choose files or a folder, run **audit only** by default, or select **guarded metadata cleanup**, which refuses detected content risks and never overwrites existing output files. Reports use file indexes rather than source paths or matched strings. The GUI does not open Office files or execute VBA.

Run `python -m pip install .` in the source folder to install the command-line and desktop entrypoints. Installable Python wheel and cross-platform source ZIP are release artifacts; this is not a native system installer.

**Security limitations:** This does NOT redact body text, sanitize VBA source, decode embedded objects, inspect images, decrypt documents, or certify any file for distribution. Risk detection is heuristic and requires qualified human review. Legacy Office formats are unsupported. Never upload classified files to a CI pipeline or public issue tracker.


## v4.1.0 Beta 1 — Office-specific privacy exposure inventory

Read-only audits now flag Excel hidden sheets/rows/columns, external links, data connections, query tables, pivot caches and hidden defined names; PowerPoint notes and hidden slides; Word linked-field candidates; custom XML, ActiveX and embedded payloads. Reports contain aggregate counts and opaque part identifiers, not extracted content. Guarded mode blocks on these indicators instead of silently deleting legitimate document structures.

**Not complete detection or redaction:** VBA macros are preserved, not executed, and VBA source is not sanitized. Password-protected, encrypted and legacy Office formats require manual handling. Classification and confidentiality clearance are outside the tool.


## v4.2.0 Beta 1 — XFCE installation and updates

Install the Debian package with `sudo apt install ./office-sanitizer_4.2.0~beta1_all.deb`. Launch from the XFCE **Office** application menu or run `office-sanitizer-gui`. The package includes a scalable icon and an XFCE-specific automatic login check for new versions, rate-limited to once daily per user. A **Check updates** button is available in the GUI, or run `office-sanitizer-update --check`.

Update checks consult only the official public GitHub Releases API; no document contents are transmitted. An installable update must be newer and provide an official Debian Release asset with a SHA-256 digest. To install a verified update, run `office-sanitizer-update --install`, enter YES, and authenticate with Polkit/apt. No unattended privileged installation takes place.

**Important:** The public GitHub Releases page does not yet have a verified versioned Debian asset publisher. Until it does, automatic checks may report no installable releases. Genuine silent automatic upgrades require a signed APT repository plus opted-in unattended-upgrades. This is not yet configured; normal APT packages do not automatically track arbitrary GitHub source commits. Existing metadata-only and human review safety restrictions remain.


## v4.3.0 Beta 1 — CI-independent XFCE release engineering

This milestone hardens the optional updater (strict GitHub release asset identity, approved HTTPS redirect hosts and Debian package metadata verification), improves batch fail-closed behavior (output-directory symlink rejection and case-insensitive filename collision checks), and adds **offline-only** reproducible release packaging.

From a local checkout with Python build prerequisites already installed:

```bash
bash scripts/release_local.sh dist
cd dist && sha256sum -c SHA256SUMS
```

The release script explicitly disables pip-index access, compiles Python, runs the complete local test suite, builds the Python wheel, creates an XFCE Debian package, archives an allowlisted source ZIP excluding private files, and writes SHA-256 checksums. It neither invokes GitHub Actions nor CircleCI. The public repository retains historical CI configurations, but **do not run or rely on either CI provider without owner approval**. Normal source commits use CI-skip markers where supported.

Update checks are optional network operations only when launched by the installed user's XFCE session or manually; the **offline release build does not check for or download updates**. A GitHub Release digest is not equivalent to an independently signed publisher package. No secure unattended updates are claimed without a signed APT repository. No sanitization result clears confidential or classified document disclosure.
