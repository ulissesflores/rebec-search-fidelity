# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-08-25

Pre-DOI. No GitHub release: the first release will be the one that mints the DOI.

### Added
- Report in English (version of record) and Portuguese (full translation), same deposit.
- Instruments for all three defects, plus the Europe PMC and figure generators.
- Frozen captures: live endpoints 2026-08-25, Internet Archive 2025-09-23.
- Provenance chain over code, evidence, results, figures and paper (`PROVENANCE.json`).
- Test suite tying every published number to the frozen data, and asserting the figures
  regenerate byte-identically.
- Quality gate and its calibration, frozen before scoring (`docs/paper/QUALITY-*`).
