# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — unreleased

Correction round following a blind three-auditor panel over the deposited text, plus the first
repair this report's own instruments were built to detect. No measurement of §3 was withdrawn and
none was re-stated: what changed is what the text claims about the artefacts, and what the
instruments do when a measurement fails.

### Added
- **§5.1 Repair status.** Defect 1 was repaired. The certificate served for
  `www.ensaiosclinicos.gov.br` now carries two `subjectAltName` entries where the one measured for
  §3.2 carried one, so the interstitial no longer occurs. Measured 4 September 2026 with the new
  instrument; the repairing certificate has `notBefore = 25 Aug 2026 22:54:08 UTC`, the same day
  this report was measured and notified. Causation is explicitly not claimed. The same section
  records what did **not** change: the widget still names the non-canonical host, and defect 2 was
  re-measured as still holding.
- `code/measure_defect1_tls.py` — the instrument for defect 1. §5 promised the finding would expire
  the day the registry repaired it, but no released instrument touched TLS, so defect 1 could have
  been repaired with nothing noticing. It was.
- `code/measurement.py` — the exit convention the instruments now share, in one place.
- The reference thresholds the calibration declares are now **checked**: minimum entry count and the
  share of references from the last three years. Both were frozen in
  `docs/paper/QUALITY-CALIBRATION.md` before scoring and measured by no code, so the manuscript
  passed the instrument by the instrument's omission. The two thresholds that are judgement rather
  than arithmetic (distinct source types, mean E-E-A-T) are now printed as NOT MECHANISED rather
  than silently dropped.

### Changed
- **§3.5 no longer states a false absolute.** The text said the only archived captures of the
  endpoint carrying a query string were the three of 23 September 2025; the sealed `cdx_inventory`
  lists six. The two claims are now separated: only the 2025 trio can test the identity of the
  response, and the three captures of 5 June 2024 enter for what they do establish — the same Google
  Custom Search `cx` the report names elsewhere, 15 months before the first point at which defect 2
  is measured. The outsourcing claim now spans 5 Jun 2024 – 20 Feb 2026; defect 2 still spans
  23 Sep 2025 – 25 Aug 2026, and the two spans are kept apart in the text.
- **Exit codes: 0 / 1 / 2.** The instruments previously returned the same code for "the finding no
  longer holds" and "the measurement could not be made" — the confusion this report's own §2.1
  argues against. `measure_archive_timeline.py` had no exception handling at all. A failed run now
  exits 2 and writes `finding_confirmed: null`, never `false`.
- **Re-runs no longer overwrite sealed evidence.** The `--out` default of every instrument pointed at
  the JSON whose hash section 6 publishes, so following the report's own instructions broke the
  report's own provenance chain. Re-runs write under `output/reruns/`, and an existing file is never
  replaced without `--force`.
- **§2.1 declares eight search terms**, in two sets kept distinct: the six run against both routes
  (the set behind defect 2) and the two added only in the browser arm. §3.4 no longer says "the six
  terms above" for an arm that ran eight.
- **§3.4 no longer calls the outsourced search "the registry's own search"** — that identity is what
  the report exists to deny.
- **§6 binds each claim to the command that reproduces it**, and states plainly that the public arm
  of defect 3 is a browser enumeration and is not reproducible by command. The previous text promised
  one command per central claim and left the mapping to the reader.
- **References: 12 → 21 entries**, renumbered by order of first appearance, with the share from the
  last three years going from 2/12 to 11/21. The added references are load-bearing where cited; three
  of them bound the report's novelty claim by naming what registry meta-research does cover
  (agreement between registry entries and the publications that follow).
- The thesis is stated in the first paragraph of both the abstract and the introduction, instead of
  only in the title.

### Removed
- `docs/paper/QUALITY-AUDIT-2026-08-25.md`. It was published inside the tagged deposit and carried a
  pass mark computed over a text that the same deposit's own `quality-checks-report.json` shows to be
  15.4% shorter than the one deposited. A stale self-assessment inside the artefact it assesses is
  the defect class this round exists to remove.

## [1.0.0] — 2026-08-25

First release. This is the version deposited and assigned a DOI.

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
