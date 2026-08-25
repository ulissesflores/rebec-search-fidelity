# Quality calibration, frozen before scoring

> **Frozen on 2026-08-25, BEFORE any score was computed.** This document is the single source of
> the technical-term lexicon, the filler patterns, the thresholds and the rubric denominator.
> Editing it after the score is known is measurement fraud — if something here is wrong, the
> correction is recorded as a dated deviation in the project's internal state file, never silently.
>
> **Publication note.** This copy had ONLY two things changed for the deposit: local paths rewritten
> to repository-relative paths or to neutral descriptions of an internal artefact, and the prose
> translated from Portuguese to English. The file frozen on 2026-08-25, before any scoring, had
> SHA-256 `bede14b4bd90e2d0cd717230c2ebbbab69eee2c55f8b691a56e2ad3d5a8b6b0f`; this copy's hash is
> recorded in `docs/paper/quality-checks-report.json` and asserted by `tests/test_paper_numbers.py`.
> **No threshold, no lexicon entry and no reading of a conditional was altered** — had any been, the
> score would be void.
>
> Source rulers: the laboratory's internal academic rubric (0-1000 over six dimensions) and its
> density checker (technical depth index, filler ratio, information density).

## 1. Unit of assessment

The deposit is **one DOI with two files**:

| File | Role |
|---|---|
| `docs/paper/MANUSCRIPT-en.md` | version of record |
| `docs/paper/MANUSCRITO-pt-BR.md` | full translation |

Each file is scored **separately** — the >= 920 gate applies per file, not to the mean — and there
are **pair-level** checks that only make sense across the whole deposit (section 4.4).

## 2. Denominator: 1000. Criteria excluded as not-applicable: NONE.

Zero sub-criteria removed. The house precedent authorises excluding what the genre makes
structurally impossible, but **nothing here is impossible** — and a trimmed denominator is exactly
how a self-audit flatters itself. Where the rubric carries a conditional ("when applicable", "when
required"), the reading is declared NOW, before scoring:

| Conditional sub-criterion | Pts | Reading declared before scoring |
|---|---|---|
| Descriptive subtitle | 15 | **APPLICABLE.** The genre (a short report with a two-part title) admits a descriptive subtitle. |
| Bilingual abstract, perfect mirror | 25 | **APPLICABLE at the deposit level.** The EN+PT pair under one DOI is the mirror; what is required is verified parity (section 4.4), not a bilingual abstract inside each file. |
| Dense table when required | 20 | **APPLICABLE.** The report presents chains measured link by link; a table is required. Target: dense, 4-7 rows x 3-5 columns. |
| Diagram or figure when applicable | 20 | **APPLICABLE.** Defect 1 is a five-link causal chain; a vector figure is warranted. |
| Latin used with purpose (2-4 times) | 10 | **APPLICABLE to both files.** Not excluded: an honest deduction is more conservative than an exclusion, and inserting decorative Latin to score would be the very filler the ruler exists to catch. |

## 3. Thresholds declared before measuring

| Threshold | Value | Source |
|---|---|---|
| Total gate | **>= 920/1000 per file** | house standard for a publication-grade paper |
| Hard density cap | technical density < 100 pts => total capped at 600 | rubric, dimension 2 |
| Technical depth index (TDI) | **>= 3.0** unique concepts per 500 words | density checker |
| Filler ratio | **< 0.12** | density checker |
| Information density (global) | **>= 0.15** per 500 words | density checker |
| Minimum reference count (`N`) | **10** | Floor for the *short report* genre, fixed before counting what the manuscript had (it had 7 at the moment of freezing — the floor is deliberately above the artefact's state, so the ruler is not shaped to fit it). |
| Distinct source types | **>= 5** of 6 (paper / book / RFC-standard / agency / framework / builder's library) | rubric, dimension 3 |
| Mean E-E-A-T of references | **>= 75/100** | rubric, dimension 3 |
| References from the last 3 years (2023-2026) | **>= 50%** | rubric, dimension 3 |

## 4. Mechanical instrumentation

Single script: `code/quality_checks.py`. It runs over both files and returns JSON. It exits
non-zero if any mechanical gate fails.

### 4.1 Domain lexicon (single source)

Written **by domain** — what a reviewer in the field would write for "measuring the public search of
a clinical trial registry" — and **not** by sweeping the manuscript. Each line is one **concept**:
`canonical | form | form | ...`. The anti-gaming rule is applied at the concept level: the English
and Portuguese surface forms of one concept count **once**.

```terms
ictrp | ICTRP | International Clinical Trials Registry Platform | Plataforma Internacional de Registros de Ensaios Clinicos
rebec | ReBEC | Registro Brasileiro de Ensaios Clinicos | Brazilian Registry of Clinical Trials
who | WHO | World Health Organization | OMS | Organizacao Mundial da Saude
primary-registry | primary registry | registro primario
trial-registry | trial registry | registro de ensaios | registries | registros
clinical-trial | clinical trial | ensaio clinico | ensaios clinicos | trials | ensaios
systematic-review | systematic review | revisao sistematica | systematic reviewer | revisor sistematico
trial-registration | trial registration | registro de ensaios clinicos | registration | adesao ao registro
meta-research | meta-research | meta-pesquisa | meta-researcher | meta-pesquisador
rbr-identifier | RBR- | identificador de ensaio | trial identifier
fiocruz | Fiocruz
publication-bias | publication bias | vies de publicacao | unpublished studies | estudos nao publicados
http | HTTP
http-200 | HTTP 200 | 200
http-301 | HTTP 301 | 301
http-403 | HTTP 403 | 403
http-404 | HTTP 404 | 404
https | HTTPS | https
tls | TLS
san | SAN | subjectAltName | subject alternative name
x509 | X.509 | certificate | certificado
lets-encrypt | Let's Encrypt
hsts | HSTS | hstspreload | HSTS preload | HSTS preloading
dns | DNS
user-agent | User-Agent
robots-txt | robots.txt
csp | Content-Security-Policy | Politica de Seguranca de Conteudo
upgrade-insecure-requests | upgrade-insecure-requests | Upgrade Insecure Requests
interstitial | interstitial | aviso de seguranca | security interstitial | erro de privacidade
rest | REST
endpoint | endpoint
openapi | OpenAPI | openapi.json
datatables | DataTables
query-string | query string | consulta na URL | string de consulta
client-side | client-side | no cliente | lado do cliente
server-side | server-side | do lado do servidor | no servidor
javascript | JavaScript
google-cse | Google Custom Search | CSE | cse.js | gcse
crawler | crawler | Googlebot | Algolia Crawler | coletor | harvester
web-archive | web archive | arquivo da web | Internet Archive | Wayback
cdx | CDX
canonical-host | canonical host | host canonico
redirect | redirect | redirecionamento
widget | widget | buscador
recall | recall
precision | precision | precisao
index | index | indice | inverted index | indice invertido
false-positive | false positive | falso positivo
substring | substring | subcadeia
positive-control | positive control | controle positivo
identifier-set | sets of trial identifiers | conjuntos de identificadores | set intersection | interseccao
result-estimate | result estimate | estimativa de resultados
pagination | paging | paginada | paginando | pagination
coverage | coverage | cobertura
reproducibility | reproducibility | reprodutibilidade | reproducible | reprodutivel
byte-identical | byte-identical | byte a byte identic
sha256 | SHA-256
md5 | MD5
hash | hash | hashes
exit-code | exit code | codigo nao-zero | non-zero | exits non-zero
instrument | instrument | instrumento
silent-failure | silent failure | falha silenciosa | silently | em silencio | invisible to | invisiveis a
provenance | provenance | proveniencia
falsifiable | falsifiable | falsificavel | refutable | refutavel
headless | headless
denominator | denominator | denominador
```

### 4.2 Filler patterns

Two lists, one per language. **Hedge exemption, declared and inherited from the laboratory's
English-venue gate rules:** the ruler's hedge regex (`arguably|seems|appears|might|may|could`) is
**excluded**. In this report hedging is epistemic virtue, not padding: the open attribution in
section 3.2 and the six limitations in section 4.3 exist precisely so the text does not claim beyond
what was measured. Scoring that as filler would push the prose to overclaim.

### 4.3 Counting regexes — two mandatory adaptations

1. **Numeric bracket citations.** The report cites `[1]`, `[3,4,5]`, `[7]` — not author-year. The
   ruler's author-year regex would count **zero**, and information density would come out falsely
   low. The gate counts `[n]` and `[n,m,...]` (each bracket is one inline citation) in addition to
   the author-year pattern.
2. **Thousands separator by language.** English writes `69,877`; Portuguese writes `69.877`. The
   gate accepts both, and the pair-parity check normalises before comparing.

### 4.4 Parity and integrity checks (the whole pair)

| Gate | What fails it |
|---|---|
| `placeholders` | any `TODO`, `TBD`, `XXX`, `<...>`, `FIXME` in either file |
| `references` | an `[n]` cited with no entry; an entry never cited; numbering out of sequence |
| `sealed_numbers` | a load-bearing number in the prose diverging from the sealed JSON in `output/` |
| `hashes` | a row of the SHA-256 table diverging from `shasum -a 256` of the real file on disk |
| `pair_parity` | section numbering diverging between the English and Portuguese editions |
| `urls` | a cited URL that does not answer 2xx/3xx |
| `dois` | a cited DOI that does not resolve at Crossref |

## 5. What this gate does NOT measure

The rubric applied in this round is a **self-audit, not a blind panel**: the session was under an
explicit constraint not to open independent sub-agents, so the three fresh-context auditors of the
house precedent did not run. That is a **declared degradation, not an equivalence** — the score
measures house quality of the text, judged by someone who is also the author. A blind panel is
recommended for the journal-submission pass, and the deposit itself remains human-gated.
