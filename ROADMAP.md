# Roadmap

## 0.1.0 — current (pre-DOI)

Three defects measured on one registry, instruments released, provenance sealed.
No GitHub release exists yet: the first release will be the one that mints the DOI.

## Next, in the order the report itself names them (section 4.4)

1. **The ICTRP census.** Run the same two-armed protocol — positive control plus
   response-identity test — against the remaining WHO ICTRP primary registries and publish
   how many discriminate, how many fail silently, and for how many the protocol does not
   apply. This is what turns one measured case into a survey, and it is the single change
   that would most raise the value of this work.
2. **Cross-browser replication and mechanism isolation.** Defect 1 was observed in current
   Chrome. Firefox and Safari are untested, and the report does not determine *which*
   mechanism performs the `http`→`https` upgrade — the site's own
   `upgrade-insecure-requests` header, or the browser's automatic upgrade. Instrumenting
   the form submission itself, rather than a programmatic click, would close it.
3. **Downstream effect, not co-occurrence.** Section 4.1 reports Europe PMC co-occurrence
   counts and explicitly refuses to convert them into harm. Sampling systematic reviews
   that record having searched ReBEC, and checking whether the trials the public search
   omits are the ones those reviews missed, would replace a proxy with an effect.
4. **Recall beyond one term.** Recall was measured for `dengue` (17 records). The search
   element returns at most about a hundred results, so a term like `diabetes` (1.452
   records) is not measurable this way. A different sampling design is needed.

## Not planned

A Colab notebook. Replication here is `python run_all.py` with no dependencies beyond
pytest; a hosted notebook would add a platform to maintain without adding reach.
