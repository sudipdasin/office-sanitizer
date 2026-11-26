# Office Sanitizer v4.3.0 Beta 2 — Local verification

Date: 2026-11-26

- Python local source assembly: **118/118 tests passed**, including live-feed malicious metadata and fallback tests.
- Built Debian package `office-sanitizer_4.3.0~beta2_all.deb`, offline Python wheel, and source ZIP.
- Repeated local builds and verified versioned artifact SHA-256 checksums.
- Previewed static portal locally and validated release JSON, package hashes and wheel installation with pip offline.
- Render static distribution service: `https://office-sanitizer-xfce-live.onrender.com/`; production deploy must be separately verified after merge.
- GitHub Actions and CircleCI were **not used** for testing or publication.
- Hosted feed SHA-256 helps detect transfer errors but is not publisher signing; installation requires human approval and Polkit.
- No document uploads to the distribution website; scanner remains local and metadata-only, not a confidentiality or classification clearance.

These local tests do not certify all Office formats, VBA source sanitation, actual Microsoft Office application compatibility, or enterprise security certification.
