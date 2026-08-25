# Reproducibility contract

## Two seals, deliberately different

This artifact separates what can be re-derived from what can only be preserved.

| Seal | What it covers | What the seal proves |
|---|---|---|
| **Frozen evidence** | `data/raw/`, `output/a1-*.json` | The captures were **not altered** since capture. It does **not** prove they can be reproduced. |
| **Reproducible derivation** | `output/figures/`, every number in the report | Given the frozen captures and this code, the figures regenerate **byte-identically** and every published number recomputes. |

Both fold into one `artifact_root` (`PROVENANCE.json`), a SHA-256 Merkle-per-stage
left-fold chain. Any byte change in any sealed file changes the root.

## What cannot be re-run, and why that is the point

The live measurement of `ensaiosclinicos.gov.br` is **not** part of `run_all.py`. The
report describes a defect in a system somebody else operates, so the measurement is not
a function anyone can call twice and expect the same answer — and it should not be:

```bash
python code/measure_public_search.py     # exits non-zero once the search starts filtering
python code/measure_archive_timeline.py   # exits non-zero if the archived captures diverge
```

Those non-zero exits are the designed end of this finding. **If the registry repairs its
search, these instruments fail, and the repair — not this report — becomes the outcome of
record.** A replication harness that hid that behind a mock would be lying about what kind
of claim this is.

The Internet Archive arm has a second, permanent limit: the start date of defect 2 is
unknown and **unrecoverable**. A 2024 capture shows a client-side search widget, and a web
archive does not preserve what JavaScript rendered.

## Track 1 — light replication (default, no network)

Standard library plus pytest. Under a minute.

```bash
python -m pip install -r requirements.txt
python run_all.py
```

This regenerates both figures and checks them byte-for-byte, ties every published number
to the frozen JSONs in both languages, and verifies the provenance chain.

## Track 2 — full replication (network, non-deterministic by nature)

```bash
python code/measure_public_search.py      # live registry, both endpoints, six terms
python code/measure_archive_timeline.py    # Internet Archive, three 2025-09-23 captures
python code/measure_downstream_mentions.py      # the three co-occurrence counts of section 4.1
python -m pytest tests -m live           # cited URLs resolve; cited DOIs known to Crossref
```

Expect drift and read it correctly:

- **Response size varies between days.** An earlier run recorded 69.876 bytes; the reported
  run recorded 69.877. The page footer carries live counters. The identity that carries the
  finding is **between terms within one run**, never between days.
- **Europe PMC counts grow.** 2.798 / 1.234 / 494 on 2026-08-25. A later run returns more.
  The report states the date; `output/downstream-mentions.json` seals it.
- **The interface's own result estimate is unstable** ("approximately 38", then
  "approximately 20", same query). That is why recall is computed over identifier sets.

## Environment

Python 3.11+. `requirements.txt` is the runtime floor; `requirements.lock` is the verbatim
freeze of the environment that signed the seal. `artifact_root` is environment-independent
by construction, so a different interpreter cannot invalidate it — `verify_chain.py` reports
an interpreter difference as INFO, never as failure.

## One measurement was made by a human, and is labelled as such

Defect 1 concerns what a person experiences, so it was measured in an ordinary desktop
Chrome, not by headless automation. Three quantities come from that session and are not
recomputable: the 20 URLs enumerated for `dengue`, the unstable result estimate, and the
earlier body size. They are traced to the documents that attest them in `docs/evidence/`,
and the gate checks that traceability rather than pretending to recompute them.
