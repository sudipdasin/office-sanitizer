# Office Sanitizer v4.2.0b1 release record

- Local Python 3.13 source: **76/76 tests passed** and compileall passed.
- Debian v4.2.0~beta1 package built successfully and verified using dpkg-deb info/content and filesystem extraction.
- Extracted Debian command-line and updater entry points ran using the distro Python runtime.
- GUI launched under xvfb virtual X11 and remained open without errors until controlled termination.
- Official desktop and XFCE autostart files verified in the package.
- Security tests cover malicious download URLs, missing SHA-256 digests, corrupt download bytes, release version ordering, and size limits.
- Automatic update checks are enabled; **unattended installation is not**. A GitHub Release asset with SHA-256 digest is required to install via the updater; no current public update asset was verified.
- These are local build results; check CircleCI separately on the exact GitHub commit. The local source archive may differ from the GitHub source tree.
- Software remains metadata-only and does not certify sensitive/classified document clearance.
