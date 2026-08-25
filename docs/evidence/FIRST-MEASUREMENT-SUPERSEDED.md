# First measurement — superseded framing, valid measurements

> [!IMPORTANT]
> **CORRECTED on 2026-08-25 by the real-browser session.** The sentence this document was built
> around — *"anyone who uses the public search and concludes 'there is nothing' concluded without
> having searched"* — **is too broad and has been withdrawn**: on the canonical host, in a browser,
> the search **works** (Google Custom Search, rendered client-side). What survives, stronger and
> mechanistic, is in `docs/evidence/BROWSER-SESSION.md`.
> The **measurements** below remain valid — it is the **interpretation** that changed.
> **Do not cite this file on its own.**

It is kept in the deposit because a withdrawn claim that disappears is indistinguishable from one
that was never made, and a reader is entitled to see what was corrected.

## The measurement of 2026-08-25

Instrument: `code/measure_public_search.py` · output: `output/public-search-vs-database.json`.

| Arm | What it measures | Result |
|---|---|---|
| 1 and 2 | Public search, positive controls (`dengue`, `diabetes`) **alongside** the terms of interest (`prion`, `Creutzfeldt`, `Jakob`, `priônica`) | **HTTP 200 for all six**; **a single SHA-256** across the six responses; **69,877 bytes** each |
| 3 | The registry's own data endpoint (`/api2/api/search`), which answers properly | **discriminates**: `dengue` 17 · `diabetes` 1,452 · `prion` 1 · `Creutzfeldt` 0 · `Jakob` 0 · `priônica` 0, of 9,629 records |
| 4 | The unrecognised-parameter trap | `?q=dengue` -> **9,629 / 9,629**: the endpoint **silently ignores** the unknown parameter and returns the whole base |

Script verdict: **finding confirmed**.

## Why arms 3 and 4 exist

- **Arm 3 is what turns a complaint into a diagnosis.** It proves the **records exist and are
  queryable** — what is broken is the door the public comes through. Without it, the finding would
  be indistinguishable from "the registry is down".
- **Arm 4 is the same defect pointing the other way.** The real contract is published at
  `/api2/openapi.json` and follows the DataTables convention: the filter is `search[value]`.
  Passing `q=` or `query=` **raises no error** — the endpoint ignores it and returns all 9,629
  records, which reads as *"every term has 9,629 results"*. A silent zero and a silent infinity
  come out of the same design: **neither route says it did not understand the question.**

## Two traps, measured rather than assumed

1. **The registry's web server returns 403 to clients with no browser User-Agent.** A naive test
   collects "403 for everything" and concludes the wrong thing from a third cause. The instrument
   sends a browser User-Agent and says why, in the code itself.
2. **The single `prion` hit is a FALSE POSITIVE.** Matching is by substring: the one record
   (`RBR-3w2scz`) is a mindfulness trial for smoking cessation. Counting it without opening the
   record would err in the opposite direction — which is why the number enters the report with the
   manual inspection attached, never as a raw count.

## Reproduction in one command

```bash
python3 code/measure_public_search.py
# exit 0 = finding confirmed; 1 = the search started filtering (also a result)
```

## Declared limits

- It measures the behaviour **on 2026-08-25**. The instrument exists precisely so the date does not
  become a debt: it re-verifies and fails loudly if the site is repaired.
- It makes **no** claim of intent or negligence. It states an observable behaviour of the system
  and its epistemic consequence for people who search.
- The API contract (`data/raw/rebec-openapi.json`) was captured the same day; if the registry
  changes the contract, arm 3 fails and the instrument says so.
