# Independent, dated corroboration from the Internet Archive

> Measured 2026-08-25. Instrument: `code/measure_archive_timeline.py` ·
> output: `output/archive-timeline.json` · raw bodies: `data/raw/wayback/`.

## Why this measurement exists

The live measurement, on its own, covers **one day**. The obvious reviewer objection — and the
easiest answer from whoever operates the service — is *"you caught a maintenance window."* This
piece answers with evidence that is **not ours**: captures made by the Internet Archive, by an
archiver who was not looking for this finding, almost a year before we were.

## The finding

On **2025-09-23**, between 17:08:18 and 17:09:59 UTC — two minutes and one second — the Wayback
Machine captured **three distinct queries** against the same ReBEC search endpoint:

| Capture (UTC) | Archived URL | SHA-256 of the body |
|---|---|---|
| 2025-09-23T17:08:18Z | `.../search/query/simple?q=crohn` | `e47f39fbc73fede9f75e40ac37013d610581b4866f54d923b8f46cb76dbfca16` |
| 2025-09-23T17:09:46Z | `.../search/query/simple?q=artrite+psoriática` | **the same** |
| 2025-09-23T17:09:59Z | `.../search/query/simple?q=psoriatic+arthritis` | **the same** |

**All three responses are byte-identical** (66,525 bytes each), and **none of them contains the
searched term anywhere in the HTML**. The archive's own CDX index records the same fact
independently of our download: the `digest` field is identical across the three captures
(`A5UZZROU6SDBTUSO22VJFZUFALI6VR3E`, the archive's base32 SHA-1).

Crohn's disease and psoriatic arthritis are different conditions with different trial counts in
ReBEC itself. A working search cannot return the same response for both.

## Bracketing: since when, and until when

| Date | Evidence | Reading |
|---|---|---|
| 2024-06-05 | A capture of `?q=RBR2bzspnz` (63,813 B) already carries the **Google Custom Search** widget (`gcse`, `cse.google`) | The page embedded Google CSE at that point. **Not testable from a capture**: CSE renders in the client, and the archive preserves only the served HTML. **Declared unverified** — we claim neither that it worked nor that it did not |
| 2025-04-04 | Capture with no `?q=` (CDX digest `MDNNS75Z…`) | Bare: no query string, so it cannot test whether different terms return the same response |
| **2025-09-13** | Capture with no `?q=`, 66,525 B (CDX digest `7OGHTN2I…`) | Identical to those of 09-23 except for the footer **counters** (`Total de Ensaios Clínicos 16844` vs `16891`), which change daily |
| **2025-09-23** | The three captures above, one digest | **Search already indifferent to the term** |
| 2025-11-13 · 2026-02-20 | Captures with no `?q=` (CDX digests `NLC4B4NY…`, `KCRUWRYK…` — different from each other and from the two above) | Same page; the 2026-02-20 one grows to 66,848 B (counters) |
| **2026-08-25** | Our measurement (`output/public-search-vs-database.json`) | Six terms, HTTP 200, **a single SHA-256**, 69,877 B — and the body served today carries `gcse`, `cse.google` and a Cloudflare Turnstile widget |

So the behaviour is recorded at **two measured points eleven months apart — 2025-09-23 and
2026-08-25**. That is persistence between two points, not continuity across the interval: the only
archived captures carrying a query string are the three of 2025-09-23, and the intermediate captures
(2025-04-04, 2025-09-13, 2025-11-13, 2026-02-20) are *bare*, retrieved without `?q=`. A bare capture
cannot test whether different terms return the same response, and their CDX digests differ from one
another for exactly that reason. They are therefore **not** corroboration, and an earlier version of
this document called them consistent and uncontradicted, which claimed more than they can show.

## What this authorises saying, and what it does not

**Authorises:** the behaviour is not episodic and not a maintenance window on the day we measured;
it is present at a point eleven months earlier, recorded by an independent third party.

**Authorises:** the start date of the defect is **unknown and earlier than 2025-09-23**. The upper
bound is what the measurement supports; the lower bound is not.

**Does not authorise** claiming the search *never* worked. The 2024-06-05 capture shows a
client-side Google search widget whose results the archive does not preserve. **A client-side
search cannot be tested retroactively** — and that is written down rather than inferred.

**Does not authorise** any claim of intent, negligence or fault. It states a dated, observable
behaviour of the system and its epistemic consequence for people who search.

## Reproduction in one command

```bash
python3 code/measure_archive_timeline.py
# exit 0 = corroboration confirmed; 1 = the captures ceased to be identical
```
