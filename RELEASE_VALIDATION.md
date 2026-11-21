# Office Sanitizer v4.1.0b1 — Release verification

Date: 2026-11-22

## Verified locally
- Assembled Community source: Python regression suite **64/64 passed** including six synthetic exposure tests and two tests using generated real Office OOXML files (hidden Excel sheet, PowerPoint speaker notes).
- Python bytecode compilation succeeded.
- A pure-Python versioned wheel built and installed; command-line entrypoint loaded.
- A Debian/Ubuntu all-architecture package built using `scripts/build_deb.sh`; Debian package metadata and contents inspected.
- Private Pro-only triage module: **8 local tests passed**; conservative fail-closed prioritization, no secret values in reports.

## Trust boundary and release gates
- These local source assemblies may differ in whitespace/docs from the exact GitHub tree. Hosted CI passing on the commit is separate evidence.
- Heuristic scan only; **no comprehensive sensitive-content redaction, VBA source rewriting, classification clearance, or certification**.
- Broad Microsoft Office/LibreOffice versions, file types and install environments have not been independently validated for this version.
- No signed native installer or GitHub Release asset published. CircleCI artifacts are versioned build outputs when CI succeeds.
- Community retains GPLv3; Pro proprietary code remains private, with distribution subject to licensing review.

Release gate: https://github.com/sudipdasin/office-sanitizer/issues/1
