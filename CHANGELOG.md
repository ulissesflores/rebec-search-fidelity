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

## [Unreleased]

Factual-correction round following external scrutiny of the manuscript. Scope was a closed
list; nothing outside it was changed. No new measurement was taken and none was withdrawn.

### Changed
- Title and abstract no longer count the defects. Defects 2 and 3 are stated as consequences
  of the single decision to outsource the search; defect 1 as where that decision meets a
  separate certificate configuration.
- §3.3 no longer says the server "ignores the query string entirely". What was measured is
  that the served body does not vary with the query string; the server's internal handling
  was not measured and is no longer asserted.
- §3.5 no longer offers the intermediate Internet Archive captures as corroboration. They are
  *bare* — retrieved without a query string — so they cannot test response identity between
  terms. The finding is now stated as two measured points eleven months apart, not a series.
  `docs/evidence/ARCHIVE-TIMELINE.md` carries the same correction.
- §4.1 declares that the route by which people reach the registry's records was not measured:
  the WHO ICTRP portal aggregates the same records and was not tested, and the methodological
  review cited for registry searching searched that portal rather than the national site.
- Reference [2] (Woolley et al.) is cited for what it says — a call for registry search
  filters that current interfaces do not offer — not for a report of search failure.
- Reference [3] notes that the 2009 announcement uses the earlier acronym *Rebrac*.
- All measurement dates declare UTC.
- §5 rewritten: notification of the registry operator now precedes deposit rather than
  following publication, sent to the address the registry publishes and to the operating
  foundation's institutional Citizen Information Service. No response is awaited and none is
  treated as consent. The section states that no formal access-to-information protocol was
  filed, rather than implying a receipt that is not held. The operator's contact address and
  the site's 404 routes were removed from the section as gratuitous to the metric.

### Removed
- The count of result URLs paged through for `dengue`. It was recorded in the browser session
  but never written to a sealed artefact, and sealing it after the fact would manufacture the
  evidence. The recall figure is set arithmetic over identifiers and does not depend on it.
