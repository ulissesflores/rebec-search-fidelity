# The real-browser session, and what it changed about the finding

> Measured 2026-08-25 in a real, logged-in **Chrome** — never a headless automation
> framework — together with TLS, DNS and the published configuration of the search widget,
> from the command line. This document **corrects** the framing of
> `docs/evidence/FIRST-MEASUREMENT-SUPERSEDED.md`.

## The earlier claim was too broad, and has been withdrawn

The first measurement concluded: *"anyone who uses the public search of ReBEC and concludes
'there is nothing about X' concluded it without having searched."*

**In a browser, for a visitor who reaches the canonical URL, the search works** — results are
rendered client-side by a Google Custom Search. The old sentence would have been refuted with
a screenshot. **It is withdrawn**, and the withdrawal is stated inside the report itself
rather than quietly dropped.

What survives is better, because it is mechanistic and every link was measured.

## What the search actually is

The public search **does not query the registry database**. The search box on the home page is
a `gcse-searchbox-only` widget of **Google Custom Search** (`cx=ad5f3224a2a0fa826`), and the
results page carries `gcse-searchresults-only`. The registry's earlier native search forms are
still present in the served HTML but enclosed in comments, one of them carrying the developer's
own note: `<!-- comentando busca antiga` ("commenting out the old search").

So what a member of the public queries is **Google's index of the website's pages**, not the
registry's 9,629 records.

## Defect 1 — the registry's own search box ends on a browser security warning

Reproduced in real Chrome: typing `dengue` into the home-page box and pressing Enter navigates to
`https://www.ensaiosclinicos.gov.br/search/query/simple?q=dengue`, and Chrome shows a **privacy
error**. The search never runs.

Each link of the chain, measured independently:

| Link | Measurement |
|---|---|
| The widget sends the visitor to the `www` host, over `http` | `https://cse.google.com/cse.js?cx=ad5f3224a2a0fa826` contains, as the only URL for this site: `http://www.ensaiosclinicos.gov.br/search/query/simple` |
| The `www` host resolves to the same server | `dig +short www.ensaiosclinicos.gov.br` -> `ensaiosclinicos.gov.br.` -> `140.82.26.58` |
| The certificate does **not** cover the `www` host | `openssl s_client -servername www.ensaiosclinicos.gov.br` -> `subject=CN=ensaiosclinicos.gov.br`, **single SAN `DNS:ensaiosclinicos.gov.br`** (Let's Encrypt, valid 2026-07-04 to 2026-10-02). `curl` refuses: *"no alternative certificate subject name matches target host name"* |
| The server would fix it itself, if asked over `http` | `curl -I http://www.ensaiosclinicos.gov.br/search/query/simple?q=dengue` -> **301** to `https://ensaiosclinicos.gov.br/search/query/simple?q=dengue` |
| But the browser never asks | The navigation goes out over `https` to the `www` host, meets the wrong certificate, and stops before the server can answer. No HSTS preloading is involved: `hstspreload.org/api/v2/status` returns `unknown` for both `gov.br` and `ensaiosclinicos.gov.br` |

**Which mechanism performs the `http`->`https` upgrade was NOT isolated**, and both candidates
are present: the registry itself serves `Content-Security-Policy: upgrade-insecure-requests` on
the home page and on the search page, and that specification upgrades form submissions
regardless of host; or the browser's own automatic HTTPS upgrade. A programmatic click did not
trigger navigation, so the two could not be separated. This matters in the direction that makes
the claim conservative: **if the upgrade comes from the site's own header, the defect is not
browser-specific.**

## Defect 2 — the server ignores `?q=`, which is what produces the silent zero for non-humans

On the canonical host, `?q=<anything>` returns **HTTP 200 with identical bytes**
(`output/public-search-vs-database.json`: six terms, a single SHA-256, 69,877 bytes each).
Filtering happens **in the client**, in Google's JavaScript. Consequence: **every non-JavaScript
access sees a search page that never filters** — `curl`, harvesting scripts, crawlers, and the
Internet Archive (see `docs/evidence/ARCHIVE-TIMELINE.md`: three distinct terms archived within
two minutes, one SHA-256, eleven months before this session — a second measured point, not a
continuous series).

**HTTP 200 is not itself the defect.** 200 is the correct status for a page that renders a form.
The defect is that the page presents itself as a search result and never filters server-side.

## Defect 3 — what the public search delivers is not what the registry holds

Measured for `dengue`, by identifier set on both sides — never by Google's own estimate:

| Source | Result |
|---|---|
| Registry database (`/api2/api/search`, `search[value]=dengue`) | **17 trials** |
| Public search (Google CSE, real Chrome, paged to exhaustion over 3 pages) | **16 distinct `RBR-` identifiers** across 20 result URLs |

> The count of 20 result URLs is recorded here because this document is the record of the session.
> It is **not** published in the report: unlike the identifier sets, the URL list was never written
> to a sealed artefact, and reconstructing it now would manufacture the evidence after the fact. The
> recall figure does not depend on it — it is set arithmetic over the identifiers.

| Intersection | **14** |
| **Recall = 14/17 = 82.4%** | |

**The three the public search does not deliver, inspected one by one:**

- `RBR-69pf3b` and `RBR-7gstxs6`: the public trial page exists (HTTP 200) **and contains the word
  `dengue`**, and the registry's own search still does not return it. These are **attributable
  index failures**.
- `RBR-5vpyh4`: the page exists but does **not** contain `dengue` in its HTML — the database
  matched on a field the public page does not display. A text index could not have found it; the
  failure is of a different kind (what the database indexes is not what the page publishes), and
  it is **not counted** as an index failure.

**Two go the other way** (`RBR-7jmj48v`, `RBR-84nk5q6`): surfaced by the public search, not
returned by the database filter for that term, and their pages do not contain the term. Recorded
as divergence in both directions, not only one.

**Google's own estimate is unstable and is not cited:** the same query returned *"approximately
38 results"* on first render and *"approximately 20"* on the two subsequent runs. The
**identifier set**, by contrast, was **identical across the two independent runs** (16 ids, 20
URLs). That is why the measurement is by identifier, never by the number the interface displays.

## Both routes agree on the terms that return nothing

`prion`, `Creutzfeldt`, `Jakob`, `priônica`, `doença priônica` and `príon` all return *"A pesquisa
não encontrou resultados"* in the browser as well. This matches the data endpoint (`Creutzfeldt`
0, `Jakob` 0, `priônica` 0; the single `prion` hit is a substring false positive, `RBR-3w2scz`, a
smoking-cessation trial). Positive controls in the browser: `dengue` and `diabetes` return results.

## What this authorises saying, and what it does not

**Authorises:** the public search of a WHO ICTRP primary registry does not query the registry's
own database — it delegates to a third-party index whose coverage is measurable and, in the one
case measured, incomplete (14/17 for `dengue`, two omissions attributable to index failure).

**Authorises:** the search box on the registry's own site sends a Chrome visitor to a browser
security warning, through a mismatch between the URL configured in the widget (`http://www.`) and
the certificate (single SAN, no `www`).

**Authorises:** every non-JavaScript access — archiving and automated harvesting included —
receives a search page that never filters, a behaviour the Internet Archive has recorded for at
least 11 months.

**Does not authorise** saying "whoever searches finds nothing": on the canonical host, in a
browser, they do. **Does not authorise** any claim of intent, negligence or fault. **Does not
authorise** generalising defect 1 beyond current Chrome, nor attributing the upgrade to the
browser rather than the site's own header.

## Reproduction

```bash
# defect 1 (causal chain, no browser needed)
curl -s "https://cse.google.com/cse.js?cx=ad5f3224a2a0fa826" | grep -o "http://www.ensaiosclinicos[^\"]*"
echo | openssl s_client -connect www.ensaiosclinicos.gov.br:443 \
  -servername www.ensaiosclinicos.gov.br 2>/dev/null | openssl x509 -noout -ext subjectAltName

# defect 2
python3 code/measure_public_search.py
python3 code/measure_archive_timeline.py

# defect 3, database side (the browser side requires real Chrome)
curl -s "https://ensaiosclinicos.gov.br/api2/api/search?draw=1&start=0&length=200&search%5Bvalue%5D=dengue" \
  -A "Mozilla/5.0" -H "Referer: https://ensaiosclinicos.gov.br/" | python3 -m json.tool | grep '"rbr"'
```

Raw captures: `data/raw/cse.js` · derived identifier sets:
`data/derived/database-dengue-ids.json`, `data/derived/recall-dengue.json`.
