#!/usr/bin/env python3
"""Measure whether the public search of ReBEC returns what its database holds.

The public search endpoint answers HTTP 200 for any query and returns a
byte-identical body. Somebody who uses it and concludes "there is nothing"
concluded without having searched.

The measurement has four arms, and the third is what makes the argument close:

1. **Positive control on the public search** -- a term that is known to have
   records (``dengue``). Without one, an empty result cannot distinguish "there
   is nothing" from "the search did not run".
2. **Terms of interest on the public search** (``prion``, ``Creutzfeldt``). If
   their bytes equal the control's, the search did not search.
3. **The registry's own data endpoint** (``/api2/api/search``), which answers
   properly -- proving the records exist and that what is broken is the door the
   public comes through.
4. **The unrecognised-parameter trap**, measured rather than asserted. The data
   endpoint follows the DataTables convention, where the filter is
   ``search[value]``. Passing ``q=`` raises no error: the endpoint ignores the
   unknown parameter and returns the whole base, which reads as "every term has
   9,629 results". That is the same silent zero pointing the other way.

Exit code 0 if the finding held on this run, 1 if it did NOT -- the search having
started to filter is also a result, and must not be swallowed.

Usage
-----
``python3 code/measure_public_search.py [--out output/public-search-vs-database.json]``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PUBLIC_SEARCH = "https://ensaiosclinicos.gov.br/search/query/simple"
DATA_ENDPOINT = "https://ensaiosclinicos.gov.br/api2/api/search"

# A browser User-Agent here is not cosmetic and not an attempt to misrepresent:
# the registry's web server answers 403 to clients that do not send one, so
# without it the whole measurement would record "403 for everything" and would be
# reporting a third cause.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
TIMEOUT = 60

# `dengue` and `diabetes` are the positive controls: endemic and highly prevalent
# in Brazil, with many registered trials. If either returned zero, the problem
# would be the base, not the term. `prion` returns a single hit that manual
# inspection shows to be a substring false positive (RBR-3w2scz, a
# smoking-cessation trial); counting it without opening the record would err in
# the opposite direction.
TERMS = ["dengue", "diabetes", "prion", "Creutzfeldt", "Jakob", "priônica"]


def fetch(url: str, params: dict, attempts: int = 3) -> tuple[int | None, bytes]:
    """GET with backoff, returning ``(status, body)`` and never raising.

    Parameters
    ----------
    url : str
        Endpoint to request.
    params : dict
        Query parameters, urlencoded onto the endpoint.
    attempts : int
        Retries before giving up, with exponential backoff.

    Returns
    -------
    tuple[int | None, bytes]
        HTTP status and body. Status is ``None`` when the request never
        completed, so an unstable network cannot be mistaken for a finding.
    """
    target = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Referer": "https://ensaiosclinicos.gov.br/",
    }
    for n in range(attempts):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(target, headers=headers), timeout=TIMEOUT
            ) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:
            if n == attempts - 1:
                return None, str(e).encode()
            time.sleep(2**n)
    return None, b""


def digest(body: bytes) -> dict:
    """Size and both digests of a response body, so a reader can re-verify it."""
    return {
        "bytes": len(body),
        "md5": hashlib.md5(body).hexdigest(),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def main() -> int:
    """Run the four arms, write the report, and return a shell exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="output/public-search-vs-database.json")
    args = ap.parse_args()

    out: dict = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "public_search": {},
        "registry_database": {},
    }

    # arms 1 and 2: the public search, control alongside term of interest
    for term in TERMS:
        status, body = fetch(PUBLIC_SEARCH, {"q": term})
        out["public_search"][term] = {"http": status, **digest(body)}

    bodies = out["public_search"].values()
    identical = len({v["sha256"] for v in bodies}) == 1
    all_200 = all(v["http"] == 200 for v in bodies)

    # arm 3: the registry's own data endpoint, which answers properly
    for term in TERMS:
        status, body = fetch(
            DATA_ENDPOINT, {"draw": 1, "start": 0, "length": 1, "search[value]": term}
        )
        record = {"http": status, **digest(body)}
        try:
            parsed = json.loads(body)
            record["recordsFiltered"] = parsed.get("recordsFiltered")
            record["recordsTotal"] = parsed.get("recordsTotal")
        except Exception:
            record["recordsFiltered"] = record["recordsTotal"] = None
        out["registry_database"][term] = record

    filtered = {t: v.get("recordsFiltered") for t, v in out["registry_database"].items()}
    discriminates = len({v for v in filtered.values() if v is not None}) > 1

    # arm 4: the unrecognised-parameter trap, measured rather than asserted
    _, trap_body = fetch(DATA_ENDPOINT, {"q": "dengue"})
    try:
        parsed = json.loads(trap_body)
        out["unrecognised_parameter"] = {
            "parameter": "q",
            "recordsFiltered": parsed.get("recordsFiltered"),
            "recordsTotal": parsed.get("recordsTotal"),
            "returns_whole_database": parsed.get("recordsFiltered") == parsed.get("recordsTotal"),
        }
    except Exception:
        out["unrecognised_parameter"] = {"parameter": "q", "error": "non-JSON response"}

    out["verdict"] = {
        "public_search_returns_200_for_every_term": all_200,
        "public_search_body_identical_across_terms": identical,
        "database_discriminates_terms": discriminates,
        "records_filtered_by_term": filtered,
        "finding_confirmed": bool(all_200 and identical and discriminates),
    }

    text = json.dumps(out, indent=2, ensure_ascii=False)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)

    if out["verdict"]["finding_confirmed"]:
        print(
            "\nFINDING CONFIRMED: the public search returns the same page for every "
            "term while the registry's own endpoint discriminates.",
            file=sys.stderr,
        )
        return 0
    print(
        "\nFINDING NOT CONFIRMED on this run -- read the JSON before concluding anything.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
