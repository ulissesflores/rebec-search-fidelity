#!/usr/bin/env python3
"""Mechanical gates over the two editions of the report.

Single source of calibration: ``docs/paper/QUALITY-CALIBRATION.md``, frozen before
any scoring. The technical-term lexicon is READ from its ``terms`` block, so the
calibration document is the only place a term list lives -- two sources drift.

Gates, in order:

1. **density** -- technical depth index, filler ratio, information density, per
   edition, per language. Anti-gaming: a CONCEPT counts once however many of its
   surface forms (English or Portuguese) appear. Hedge patterns are excluded by
   the calibration: in this report hedging is the virtue, not the padding.
2. **placeholders** -- no draft marker survives into a deposit.
3. **references** -- every ``[n]`` cited has an entry, every entry is cited, the
   numbering is a run of ``1..N``, and the two reference thresholds the calibration
   declares and that a machine CAN check are checked: the minimum entry count and
   the share published in the last three years. The calibration declares two more
   (distinct source types, mean E-E-A-T) that are judgement, not arithmetic; they
   are listed in the report as NOT MECHANISED rather than silently dropped, because
   a threshold no code measures otherwise reads as a threshold that passed.
4. **sealed numbers** -- every load-bearing quantity in the prose is recomputed
   from the frozen JSONs, and required in BOTH languages.
5. **attested** -- quantities from the human browser session are not recomputable,
   so they are checked for traceability to the document that attests them.
6. **hashes** -- the SHA-256 table in section 6 is recomputed from the files on disk.
7. **pair parity** -- the two editions carry the same section skeleton.
8. **network** -- cited URLs resolve and cited DOIs are known to Crossref.

Exit 0 if every gate passed, 1 otherwise.

Usage
-----
``python3 code/quality_checks.py [--offline]``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "docs" / "paper"
EN, PT = PAPER / "MANUSCRIPT-en.md", PAPER / "MANUSCRITO-pt-BR.md"
CALIBRATION = PAPER / "QUALITY-CALIBRATION.md"
REPORT = PAPER / "quality-checks-report.json"
OUTPUT, DERIVED, EVIDENCE = ROOT / "output", ROOT / "data" / "derived", ROOT / "docs" / "evidence"

FILLER_EN = [
    r"\bit is important to (note|mention|emphasize|highlight)\b",
    r"\bit should be noted that\b",
    r"\bit is worth (noting|mentioning)\b",
    r"\bneedless to say\b",
    r"\bin order to\b",
    r"\bthe fact that\b",
    r"\bas (previously |already )?(mentioned|noted|discussed) (above|earlier|previously)\b",
    r"\bin conclusion\b",
    r"\bat the end of the day\b",
    r"\bbasically\b",
    r"\ba (wide |large )?(variety|number) of\s+\w+\s+\w+",
    r"\b(various|several|many|numerous) (studies|authors|works|papers)\b\s*(?!\()",
    r"\b(robust|modern|innovative|efficient|scalable|effective)\b(?!\s+(at|for|in|against))",
]
FILLER_PT = [
    r"\bé importante (notar|destacar|salientar|frisar)\b",
    r"\bvale (a pena |ressaltar|destacar)\b",
    r"\bde (certa |alguma )?forma\b",
    r"\bno final das contas\b",
    r"\bao fim e ao cabo\b",
    r"\bdiversos? (autores?|estudos?)\s*(?!\()",
    r"\b(como|conforme) já mencionado anteriormente\b",
    r"\bao longo do trabalho\b",
    r"\bem conclusão\b",
    r"\bpode-se afirmar que\b",
    r"\ba (maioria|grande parte) dos?\s+\w+\s+\w+",
    r"\b(robusto|moderno|inovador|eficiente|escalável|eficaz)\b(?!\s+(em|para|de|por|com))",
]

# URLs the report MEASURES rather than cites. Exempt from the reachability gate by
# construction: defect 1 is precisely that one of them does not work.
URLS_UNDER_MEASUREMENT = {
    "http://www.ensaiosclinicos.gov.br/search/query/simple",
    "https://www.ensaiosclinicos.gov.br/search/query/simple?q=dengue",
    "http://www.ensaiosclinicos.gov.br/search/query/simple?q=dengue",
    "https://ensaiosclinicos.gov.br/search/query/simple?q=dengue",
    "https://cse.google.com/cse.js?cx=ad5f3224a2a0fa826",
}

failures: list[str] = []


def fail(gate: str, message: str) -> None:
    """Record one gate failure; the run fails at the end, never mid-check."""
    failures.append(f"[{gate}] {message}")


def load_concepts() -> dict[str, list[str]]:
    """Read the frozen ``terms`` block as ``{concept: [surface forms]}``."""
    match = re.search(r"```terms\n(.*?)```", CALIBRATION.read_text(encoding="utf-8"), re.S)
    if not match:
        raise SystemExit(f"[FATAL] ```terms``` block missing from {CALIBRATION}")
    concepts = {}
    for line in match.group(1).splitlines():
        if line.strip():
            parts = [p.strip() for p in line.split("|")]
            concepts[parts[0]] = parts[1:]
    if len(concepts) < 30:
        raise SystemExit(f"[FATAL] lexicon looks wrong ({len(concepts)} concepts < 30)")
    return concepts


def load_reference_thresholds() -> dict:
    """Read the reference thresholds from the frozen calibration, never from here.

    The calibration table is the single source; duplicating a number in code is
    how a gate and its own rule drift apart.
    """
    text = CALIBRATION.read_text(encoding="utf-8")
    minimum = re.search(r"Minimum reference count[^|]*\|\s*\*\*(\d+)\*\*", text)
    recent = re.search(r"last 3 years \((\d{4})-(\d{4})\)[^|]*\|\s*\*\*>=\s*(\d+)%\*\*", text)
    if not minimum or not recent:
        raise SystemExit(f"[FATAL] reference thresholds missing from {CALIBRATION}")
    return {
        "minimum_entries": int(minimum.group(1)),
        "recent_window": [int(recent.group(1)), int(recent.group(2))],
        "recent_share_min": int(recent.group(3)) / 100,
        "declared_but_not_mechanised": [
            "distinct source types (>= 5 of 6) -- classification, not arithmetic",
            "mean E-E-A-T of references (>= 75/100) -- judgement, not arithmetic",
        ],
    }


def _entry_year(entry: str) -> int | None:
    """Publication year of one reference entry: the latest plausible year in it.

    Reference entries carry several numbers that look like years (DOI fragments,
    RFC numbers, page ranges). Bounded four-digit tokens inside the plausible
    window are the candidates, and the publication year is the latest of them --
    a DOI minted earlier than the issue, or a span such as ``2007-2013``, must not
    outrank the year the entry actually states. ``None`` for an undated resource.
    """
    years = [int(y) for y in re.findall(r"\b(\d{4})\b", entry) if 1990 <= int(y) <= 2027]
    return max(years) if years else None


def _deaccent(text: str) -> str:
    """Strip combining marks so a Portuguese form matches its unaccented spelling."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def density(text: str, concepts: dict[str, list[str]], lang: str) -> dict:
    """Measure technical depth, filler and information density for one edition."""
    words = len(re.findall(r"\b\w+\b", text))
    plain = _deaccent(text)
    found = set()
    for concept, forms in concepts.items():
        for form in forms:
            pattern = re.escape(_deaccent(form)).replace(r"\-", r"[-\s]?").replace(r"\ ", r"\s+")
            if re.search(rf"(?<![\w-]){pattern}", plain, re.IGNORECASE):
                found.add(concept)
                break
    patterns = FILLER_EN if lang == "en" else FILLER_PT
    fillers = sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)
    # calibration 4.3.1: this report cites [n] / [n,m], not author-year
    citations = len(re.findall(r"\[\d+(?:\s*,\s*\d+)*\]", text))
    citations += len(
        re.findall(r"\([A-Z][\wà-úÀ-Ú&.,\s-]{2,60}?,?\s(?:et al\.,?\s)?[12][0-9]{3}[abc]?\)", text)
    )
    # calibration 4.3.2: English 69,877 and Portuguese 69.877 are one quantity
    numbers = len(
        re.findall(
            r"\d+[,.]?\d*\s*(?:%|×|x\b|bytes|ensaios|trials|registros|records)"
            r"|\b\d{1,3}[.,]\d{3}\b|\bHTTP\s\d{3}\b|(?<![\d/])\d+/\d+(?![\d/])",
            text,
        )
    )
    tdi = (len(found) * 500) / words if words else 0
    filler_ratio = fillers / words if words else 0
    info_density = (citations + numbers) / (words / 500) if words else 0
    passed = tdi >= 3 and filler_ratio < 0.12 and info_density >= 0.15
    if not passed:
        fail("density", f"{lang}: tdi={tdi:.2f} filler={filler_ratio:.4f} info={info_density:.2f}")
    return {
        "words": words,
        "unique_concepts": len(found),
        "fillers": fillers,
        "inline_citations": citations,
        "metric_numbers": numbers,
        "tdi": round(tdi, 2),
        "filler_ratio": round(filler_ratio, 4),
        "info_density": round(info_density, 2),
        "verdict": "ok" if passed else "review",
    }


def placeholders(text: str, label: str) -> int:
    """Count draft markers that must never survive into a deposit."""
    hits = re.findall(r"\bTODO\b|\bTBD\b|\bXXX\b|\bFIXME\b|<[a-zà-ú][^>\n]{3,60}>", text)
    if hits:
        fail("placeholders", f"{label}: {hits[:5]}")
    return len(hits)


def references(text: str, label: str, heading: str) -> dict:
    """Check that citations and reference entries are a complete, ordered match."""
    body, _, listing = text.partition(f"\n## {heading}\n")
    if not listing:
        fail("references", f"{label}: section '{heading}' not found")
        return {}
    listing = listing.split("\n## ")[0]
    cited = {
        int(n) for group in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", body) for n in group.split(",")
    }
    entries = {int(n) for n in re.findall(r"^(\d+)\.\s", listing, re.M)}
    if cited - entries:
        fail("references", f"{label}: cited without an entry {sorted(cited - entries)}")
    if entries - cited:
        fail("references", f"{label}: entry never cited {sorted(entries - cited)}")
    if entries != set(range(1, len(entries) + 1)):
        fail("references", f"{label}: numbering out of sequence {sorted(entries)}")

    # The two calibration thresholds a machine can actually check. Before this
    # existed, both were declared in the calibration and measured by nothing, so
    # the manuscript passed the instrument by the instrument's omission.
    limits = load_reference_thresholds()
    blocks = [b for b in re.split(r"\n(?=\d+\.\s)", listing.strip()) if re.match(r"\d+\.\s", b)]
    years = {int(re.match(r"(\d+)\.", b).group(1)): _entry_year(b) for b in blocks}
    low, high = limits["recent_window"]
    recent = sorted(n for n, y in years.items() if y is not None and low <= y <= high)
    undated = sorted(n for n, y in years.items() if y is None)
    share = len(recent) / len(years) if years else 0.0

    if len(entries) < limits["minimum_entries"]:
        fail("references", f"{label}: {len(entries)} entries < floor {limits['minimum_entries']}")
    if share < limits["recent_share_min"]:
        fail(
            "references",
            f"{label}: {len(recent)}/{len(years)} entries from {low}-{high} "
            f"({share:.1%}) < floor {limits['recent_share_min']:.0%}",
        )

    return {
        "cited": sorted(cited),
        "entries": len(entries),
        "years": {str(n): years[n] for n in sorted(years)},
        "recent_entries": recent,
        "recent_share": round(share, 4),
        "recent_window": [low, high],
        "undated_entries": undated,
        "thresholds": {
            "minimum_entries": limits["minimum_entries"],
            "recent_share_min": limits["recent_share_min"],
        },
        "declared_but_not_mechanised": limits["declared_but_not_mechanised"],
    }


def sealed() -> dict:
    """Load every frozen JSON the published numbers resolve from."""
    files = {
        "search": OUTPUT / "public-search-vs-database.json",
        "archive": OUTPUT / "archive-timeline.json",
        "downstream": OUTPUT / "downstream-mentions.json",
        "recall": DERIVED / "recall-dengue.json",
        "repair_tls": OUTPUT / "repair-2026-09-04" / "defect1-tls.json",
        "repair_search": OUTPUT / "repair-2026-09-04" / "public-search.json",
    }
    for path in files.values():
        if not path.exists():
            raise SystemExit(f"[FATAL] sealed JSON missing: {path}")
    return {name: json.loads(path.read_text(encoding="utf-8")) for name, path in files.items()}


def _one(values: set, what: str):
    """Return the single shared value, failing loudly if the set is not a singleton."""
    if len(values) != 1:
        raise SystemExit(f"[FATAL] {what} is not identical across terms: {values}")
    return values.pop()


def _search_bytes(d: dict) -> int:
    """Body size shared by all six public-search responses."""
    return _one({v["bytes"] for v in d["search"]["public_search"].values()}, "public search size")


def _search_sha(d: dict) -> str:
    """SHA-256 shared by all six public-search responses."""
    return _one(
        {v["sha256"] for v in d["search"]["public_search"].values()}, "public search digest"
    )


def _archive_bytes(d: dict) -> int:
    """Body size shared by the three Internet Archive captures."""
    return _one({c["bytes"] for c in d["archive"]["captures_2025_09_23"]}, "capture size")


def _archive_sha(d: dict) -> str:
    """SHA-256 shared by the three Internet Archive captures."""
    return _one({c["sha256"] for c in d["archive"]["captures_2025_09_23"]}, "capture digest")


def _records(d: dict, term: str) -> int:
    """Return how many records the registry database matches for one term."""
    return d["search"]["verdict"]["records_filtered_by_term"][term]


# (english literal, portuguese literal, resolver). The resolver READS the sealed
# JSON and the gate recomputes the verdict here: a table of pre-computed booleans
# would only echo what the author already believed.
NUMBER_CHECKS = [
    ("17", "17", lambda d: _records(d, "dengue")),
    ("1,452", "1.452", lambda d: _records(d, "diabetes")),
    ("9,629", "9.629", lambda d: d["search"]["registry_database"]["dengue"]["recordsTotal"]),
    ("69,877", "69.877", _search_bytes),
    ("66,525", "66.525", _archive_bytes),
    ("16", "16", lambda d: len(d["recall"]["public_search"])),
    (
        "14/17",
        "14/17",
        lambda d: f"{len(d['recall']['intersection'])}/{len(d['recall']['database'])}",
    ),
    ("2,798", "2.798", lambda d: d["downstream"]["counts"]["ReBEC"]),
    (
        "1,234",
        "1.234",
        lambda d: d["downstream"]["counts"]['"Brazilian Registry of Clinical Trials"'],
    ),
    ("494", "494", lambda d: d["downstream"]["counts"]['"ensaiosclinicos.gov.br"']),
    # §5.1: the re-measurement of 2026-09-04. Published in the prose, therefore
    # recomputed from the artefact, exactly like the numbers of §3.
    ("18", "18", lambda d: d["repair_search"]["registry_database"]["dengue"]["recordsFiltered"]),
    (
        "1,457",
        "1.457",
        lambda d: d["repair_search"]["registry_database"]["diabetes"]["recordsFiltered"],
    ),
    ("9,661", "9.661", lambda d: d["repair_search"]["registry_database"]["dengue"]["recordsTotal"]),
    (_search_sha, _search_sha, _search_sha),
    (_archive_sha, _archive_sha, _archive_sha),
]

IDENTIFIER_CHECKS = [
    ("RBR-69pf3b", "not_returned"),
    ("RBR-7gstxs6", "not_returned"),
    ("RBR-5vpyh4", "not_returned"),
    ("RBR-7jmj48v", "outside_database_filter"),
    ("RBR-84nk5q6", "outside_database_filter"),
]


def numbers(en: str, pt: str, d: dict) -> list[dict]:
    """Check every load-bearing quantity against the sealed data, in both languages."""
    rows = []
    for literal_en, literal_pt, resolve in NUMBER_CHECKS:
        value = resolve(d)
        expected_en = str(value if callable(literal_en) else literal_en)
        expected_pt = str(value if callable(literal_pt) else literal_pt)
        normalised = str(value).replace(",", "").replace(".", "")
        for label, expected, text in (("EN", expected_en, en), ("PT", expected_pt, pt)):
            if expected.replace(",", "").replace(".", "") != normalised:
                fail("sealed_numbers", f"{label} literal {expected!r} != sealed {value!r}")
            if expected not in text:
                fail("sealed_numbers", f"{label} does not contain {expected!r}")
        rows.append({"sealed": str(value), "en": expected_en, "pt": expected_pt})
    for identifier, key in IDENTIFIER_CHECKS:
        if identifier not in d["recall"][key]:
            fail("sealed_numbers", f"{identifier} is not in recall.{key}")
        for label, text in (("EN", en), ("PT", pt)):
            if identifier not in text:
                fail("sealed_numbers", f"{label} does not mention {identifier}")
    for term, expected in (("prion", 1), ("Creutzfeldt", 0), ("Jakob", 0), ("priônica", 0)):
        if _records(d, term) != expected:
            fail(
                "sealed_numbers",
                f"records for {term!r}: sealed={_records(d, term)} != {expected} in the prose",
            )
    return rows


# Quantities from the human browser session: not recomputable, so traced instead. The count of
# result URLs the session paged through was dropped from the report rather than traced: it lived
# only in the session and sealing it after the fact would manufacture the evidence.
ATTESTED = [("38", "38"), ("69,876", "69.876")]
ATTESTING_DOCUMENTS = [EVIDENCE / "BROWSER-SESSION.md", EVIDENCE / "EARLIER-MEASUREMENT.md"]


def attested(en: str, pt: str) -> list[dict]:
    """Trace the human-observed quantities to the documents that attest them."""
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in ATTESTING_DOCUMENTS if p.exists())
    plain = corpus.replace(".", "").replace(",", "")
    rows = []
    for literal_en, literal_pt in ATTESTED:
        traced = literal_en.replace(",", "").replace(".", "") in plain
        if not traced:
            fail("attested", f"{literal_en!r} is not traceable to any evidence document")
        if literal_en not in en:
            fail("attested", f"EN does not contain {literal_en!r}")
        if literal_pt not in pt:
            fail("attested", f"PT does not contain {literal_pt!r}")
        rows.append({"value": literal_en, "traced": traced})
    return rows


HASH_TABLE = {
    "code/measurement.py": ROOT / "code" / "measurement.py",
    "code/measure_public_search.py": ROOT / "code" / "measure_public_search.py",
    "output/public-search-vs-database.json": OUTPUT / "public-search-vs-database.json",
    "code/measure_archive_timeline.py": ROOT / "code" / "measure_archive_timeline.py",
    "output/archive-timeline.json": OUTPUT / "archive-timeline.json",
    "code/measure_defect1_tls.py": ROOT / "code" / "measure_defect1_tls.py",
    "code/measure_downstream_mentions.py": ROOT / "code" / "measure_downstream_mentions.py",
    "output/downstream-mentions.json": OUTPUT / "downstream-mentions.json",
    "output/repair-2026-09-04/defect1-tls.json": OUTPUT / "repair-2026-09-04" / "defect1-tls.json",
    "output/repair-2026-09-04/public-search.json": OUTPUT
    / "repair-2026-09-04"
    / "public-search.json",
    "output/repair-2026-09-04/ct-log-ensaiosclinicos.json": OUTPUT
    / "repair-2026-09-04"
    / "ct-log-ensaiosclinicos.json",
    "code/make_figure.py": ROOT / "code" / "make_figure.py",
    "output/figures/fig1-defect1-chain.svg": OUTPUT / "figures" / "fig1-defect1-chain.svg",
    "output/figures/fig1-defect1-chain-pt.svg": OUTPUT / "figures" / "fig1-defect1-chain-pt.svg",
}


def hashes(en: str, pt: str) -> list[dict]:
    """Recompute the section 6 hash table from the files on disk."""
    rows = []
    for label, path in HASH_TABLE.items():
        if not path.exists():
            fail("hashes", f"file missing: {path}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        for edition, text in (("EN", en), ("PT", pt)):
            if actual not in text:
                printed = re.search(rf"`{re.escape(label)}`\s*\|\s*`([0-9a-f]{{64}})`", text)
                fail(
                    "hashes",
                    f"{edition}: {label} "
                    f"table={printed.group(1) if printed else '?'} disk={actual}",
                )
        rows.append({"file": label, "sha256": actual})
    return rows


def parity(en: str, pt: str) -> dict:
    """Compare the section skeletons of the two editions."""

    def skeleton(text: str) -> list[str]:
        """Section numbering and heading depth, language-independent."""
        return [f"{h}{n}" for h, n in re.findall(r"^(#{2,3})\s+(\d+(?:\.\d+)*)\.?\s", text, re.M)]

    a, b = skeleton(en), skeleton(pt)
    if a != b:
        fail("pair_parity", f"section skeletons diverge: EN={a} PT={b}")
    return {"sections": a, "identical": a == b}


def _status(url: str) -> int:
    """HTTP status for one URL, or 0 when the request could not complete."""
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) quality_checks"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def network(en: str, pt: str) -> dict:
    """Check that cited URLs resolve and cited DOIs are known to Crossref."""
    urls, dois = set(), set()
    for text in (en, pt):
        # fenced blocks hold shell snippets, not citations: a grep pattern such as
        # "http://www.ensaiosclinicos[^\"]*" is not a URL to reach.
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        urls |= {u.rstrip(").,;·") for u in re.findall(r"https?://[^\s)\]\[<>`\"]+", prose)}
        dois |= set(re.findall(r"doi:(10\.\d{4,9}/[^\s·]+)", text))
    urls -= URLS_UNDER_MEASUREMENT

    url_rows = []
    for url in sorted(urls):
        code = _status(url)
        if not 200 <= code < 400:
            fail("urls", f"{url} -> HTTP {code}")
        url_rows.append({"url": url, "http": code})

    doi_rows = []
    for doi in sorted(dois):
        code = _status(f"https://api.crossref.org/works/{doi}/agency")
        if code != 200:
            fail("dois", f"{doi} -> Crossref HTTP {code}")
        doi_rows.append({"doi": doi, "crossref_http": code})
    return {"urls": url_rows, "dois": doi_rows}


def published_root() -> dict:
    """Tie every artifact_root printed in README.md to the one in PROVENANCE.json.

    v1.1.0 shipped a README quoting the root of the 2026-08-25 seal, two seals
    stale, and nothing noticed: the chain verifies the files it seals, and the
    README is not one of them. A root printed for a reader is a claim about the
    artefact like any other, so it is checked like any other.
    """
    root = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))["artifact_root"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quoted = set(re.findall(r"\b([0-9a-f]{64})\b", readme)) | {
        m + "..." for m in re.findall(r"\b([0-9a-f]{16})(?=\.\.\.)", readme)
    }
    stale = sorted(q for q in quoted if not root.startswith(q.rstrip(".")))
    for q in stale:
        fail("published_root", f"README quotes {q}, PROVENANCE.json has {root}")
    return {"provenance_root": root, "quoted_in_readme": sorted(quoted), "stale": stale}


def main() -> int:
    """Run every gate, write the report, and return a shell exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="skip the network gates")
    args = ap.parse_args()

    en, pt = EN.read_text(encoding="utf-8"), PT.read_text(encoding="utf-8")
    concepts = load_concepts()
    data = sealed()

    report = {
        "calibration": {
            "file": str(CALIBRATION.relative_to(ROOT)),
            "sha256": hashlib.sha256(CALIBRATION.read_bytes()).hexdigest(),
            "concepts_in_lexicon": len(concepts),
        },
        "density": {"en": density(en, concepts, "en"), "pt": density(pt, concepts, "pt")},
        "placeholders": {"en": placeholders(en, "EN"), "pt": placeholders(pt, "PT")},
        "references": {
            "en": references(en, "EN", "References"),
            "pt": references(pt, "PT", "Referências"),
        },
        "sealed_numbers": numbers(en, pt, data),
        "attested": attested(en, pt),
        "hashes": hashes(en, pt),
        "published_root": published_root(),
        "pair_parity": parity(en, pt),
        "network": {"skipped": True} if args.offline else network(en, pt),
    }
    report["failures"] = failures
    report["verdict"] = "PASS" if not failures else "FAIL"

    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"\n-> {REPORT}\n-> verdict: {report['verdict']} ({len(failures)} failures)")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
