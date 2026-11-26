# Office Sanitizer v4.3.0 Beta 1 — local release validation

Date: 2026-11-26

## Local verification
- 100/100 Python tests passed against locally assembled Community v4.3 source (includes original v4.2 source snapshot plus the new updater, batch, packaging, and regression changes).
- Python compilation passed.
- Built locally without GitHub Actions or CircleCI: `office-sanitizer_4.3.0~beta1_all.deb`, `office_sanitizer-4.3.0b1-py3-none-any.whl`, `office-sanitizer-4.3.0b1-source.zip` and `SHA256SUMS`.
- SHA-256 manifest verified all three local artifacts with `sha256sum -c`.
- Debian control metadata: package `office-sanitizer`, version `4.3.0~beta1`, architecture `all`. XFCE menu and login update-check launchers present.
- GUI stayed active under Xvfb until intentional timeout, with no reported startup error. This is a smoke test, not full desktop UX certification.
- Regression cases include hostile release URLs, external redirects, wrong Debian metadata, symlinked output directories, filename collisions, reproducible archives, and source-archive symlink confidentiality.

## Provenance and policy
- Earlier local source ZIP content is not guaranteed identical to GitHub's full repository tree. These local tests do **not** establish that the exact post-merge GitHub commit passed an automated pipeline.
- Owner instruction: do not trigger, dispatch, rerun or rely on GitHub Actions or CircleCI unless explicitly reauthorized. This release uses local tests and local packaging only.
- No GitHub Release asset or signed APT repository has been published. Update checks alone cannot provide automatic installation from unverified/unpublished releases.
- GitHub Releases SHA-256 digest protects transfer integrity, not independent publisher authenticity. A signed APT repository is required for a higher-assurance unattended-upgrade mechanism.
- This remains a metadata-only sanitizer and heuristic risk-audit tool. No complete content/VBA sanitization, Microsoft Office certification, or confidential/classified-document disclosure clearance is claimed.

## Local artifact checksums
```text
4c2e4f8c4b83d01dbd17d33608a10fc12690e702da503dea3fa08b132f1d0fcc  office-sanitizer_4.3.0~beta1_all.deb
624becb5825751f51788e4abc776e6de47f2c9f003a0b31a6169b3b2d3845259  office_sanitizer-4.3.0b1-py3-none-any.whl
9b2a060e54f8e5300ab9a5d0e74a98c39f8db6e0f83063f795929a6a922c6cbe  office-sanitizer-4.3.0b1-source.zip
```
