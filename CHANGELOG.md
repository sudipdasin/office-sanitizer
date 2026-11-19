# Changelog

## 1.0.0 — 2026-11-19
- Added conservative OOXML metadata-only engine, atomic output, fail-closed format handling, ZIP checks and macro SHA-256 comparisons.
- Added CLI, CircleCI test config, regression tests and explicit security limitations.

## 2.0.0a1 — 2026-11-19
- Add read-only OOXML risk inventory for PII indicators, VBA presence, embedded parts, hidden markers, revisions and external references.
- Expose `--audit` via CLI and six new regression tests.
- 12 tests passed in locally assembled v1+v2 code; hosted CI and Office application compatibility remain unverified.
- Not a certified sanitizer for confidential or classified document release.
