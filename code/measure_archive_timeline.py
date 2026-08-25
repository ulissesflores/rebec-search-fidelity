#!/usr/bin/env python3
"""Corroborate the finding independently, through the Internet Archive.

``measure_public_search.py`` measures the public search of ReBEC today. This asks
a different question: for how long has it behaved this way, and is there a record
of it made by a third party who was not looking for the finding?

The Internet Archive captured three distinct queries against the same endpoint on
2025-09-23, within two minutes of one another. If the search worked, the three
captures would differ. That is the whole test.

Exit code 1 if the captures cease to be identical -- if the premise of the test
falls, the date claim must not quietly survive it.

Usage
-----
``python3 code/measure_archive_timeline.py [--out output/archive-timeline.json]``
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import sys
import urllib.parse
import urllib.request

# The registry's server and archive.org itself answer differently to clients with
# no browser User-Agent; it is declared here so the test does not measure a third
# cause instead of the one it is about.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
CDX = "http://web.archive.org/cdx/search/cdx"
BASE = "https://ensaiosclinicos.gov.br/search/query/simple"

# The three captures of 2025-09-23, with the terms the archiver used.
CAPTURES = [
    ("20250923170818", "crohn"),
    ("20250923170946", "artrite psoriática"),
    ("20250923170959", "psoriatic arthritis"),
]


def get(url: str, timeout: int = 60) -> bytes:
    """Fetch a URL and return the raw body."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as r:
        return r.read()


def snapshot(timestamp: str, term: str) -> dict:
    """Download one capture verbatim and describe it.

    The ``id_`` suffix asks the Wayback Machine for the body as it was stored,
    without the archive's own banner, so the digest is of the registry's bytes.

    Parameters
    ----------
    timestamp : str
        Wayback timestamp, ``YYYYMMDDhhmmss``.
    term : str
        The query the archiver used, which the response should reflect and does not.

    Returns
    -------
    dict
        Timestamp, term, size, SHA-256, and whether the searched term appears at
        all in the returned HTML.
    """
    target = f"{BASE}?q={urllib.parse.quote_plus(term)}"
    body = get(f"https://web.archive.org/web/{timestamp}id_/{target}")
    if body[:2] == b"\x1f\x8b":  # the archive returns the body as it stored it
        body = gzip.decompress(body)
    text = body.decode("utf-8", "replace").lower()
    return {
        "timestamp": timestamp,
        "term": term,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "term_present_in_html": term.split()[0].lower() in text,
    }


def cdx_inventory() -> list[dict]:
    """List the archive's own index entries for this endpoint.

    The CDX index records one digest per capture, computed by the archive rather
    than by us -- so the identity of the three captures can be checked without
    trusting our download.
    """
    query = urllib.parse.urlencode(
        {
            "url": "ensaiosclinicos.gov.br/search/query/simple*",
            "output": "json",
            "fl": "timestamp,statuscode,digest,original",
            "limit": 200,
        }
    )
    rows = json.loads(get(f"{CDX}?{query}").decode())
    return [dict(zip(rows[0], row, strict=False)) for row in rows[1:]]


def main() -> int:
    """Fetch the three captures, compare them, write the report, return an exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="output/archive-timeline.json")
    args = ap.parse_args()

    captures = [snapshot(ts, term) for ts, term in CAPTURES]
    digests = {c["sha256"] for c in captures}
    identical = len(digests) == 1
    no_term_present = not any(c["term_present_in_html"] for c in captures)

    report = {
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Internet Archive Wayback Machine (independent third party)",
        "captures_2025_09_23": captures,
        "cdx_inventory": cdx_inventory(),
        "verdict": {
            "three_distinct_terms_same_response": identical,
            "single_sha256": next(iter(digests)) if identical else None,
            "no_capture_contains_its_own_term": no_term_present,
            "corroboration_confirmed": identical and no_term_present,
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(report["verdict"], ensure_ascii=False, indent=2))
    return 0 if report["verdict"]["corroboration_confirmed"] else 1


if __name__ == "__main__":
    sys.exit(main())
