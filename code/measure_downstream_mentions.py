#!/usr/bin/env python3
"""Seal the three Europe PMC co-occurrence counts quoted in section 4.1.

These are NOT claims that the works searched ReBEC. They are literal hit counts
for three strings, used in the report only as a crude indication of how much
downstream work sits near this interface -- which is why the report refuses to
convert them into an estimate of harm.

Re-running on a later date returns larger numbers, because the index grows. The
report states the measurement date, so the sealed file records it too.

Usage
-----
``python3 code/measure_downstream_mentions.py``  ->  ``output/downstream-mentions.json``
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
QUERIES = ["ReBEC", '"Brazilian Registry of Clinical Trials"', '"ensaiosclinicos.gov.br"']


def hits(query: str) -> int:
    """Return Europe PMC's total hit count for one query string."""
    url = f"{API}?query={urllib.parse.quote(query)}&format=json&pageSize=1"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)["hitCount"]


def main() -> None:
    """Query the three strings and write the sealed report."""
    report = {
        "generated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Europe PMC REST search (hitCount)",
        "endpoint": API,
        "counts": {q: hits(q) for q in QUERIES},
    }
    dest = ROOT / "output" / "downstream-mentions.json"
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
