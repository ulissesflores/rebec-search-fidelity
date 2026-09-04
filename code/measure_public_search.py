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

Exit codes (see ``code/measurement.py``): 0 the finding held, 1 it did not -- the
search having started to filter is also a result and must not be swallowed -- and
2 the measurement could not be made, which says nothing about the finding. The
third code exists because this report's own argument (§2.1) is that a failed
measurement and a negative result must never share a signal.

The default ``--out`` deliberately does NOT point at the JSON whose hash the
report publishes: following these instructions must not break the seal.

Usage
-----
``python3 code/measure_public_search.py [--out output/reruns/public-search-vs-database.json]``
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

from measurement import EXIT_MEASUREMENT_FAILED, add_out_argument, report_outcome, write_report

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
    add_out_argument(ap, "output/reruns/public-search-vs-database.json")
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

    # Validity BEFORE verdict, and by the same rule the report applies to the
    # registry: a request that never completed, or a positive control that comes
    # back empty, means the measurement did not happen. Reporting that as
    # "the finding no longer holds" would commit the very confusion of §2.1.
    unreachable = sorted(
        t
        for section in ("public_search", "registry_database")
        for t, v in out[section].items()
        if v["http"] is None
    )
    controls = {t: filtered.get(t) for t in ("dengue", "diabetes")}
    controls_have_records = all(isinstance(n, int) and n > 0 for n in controls.values())
    valid = not unreachable and controls_have_records

    out["measurement"] = {
        "valid": valid,
        "requests_that_never_completed": unreachable,
        "positive_controls_records": controls,
        "positive_controls_have_records": controls_have_records,
        "why": (
            "valid"
            if valid
            else "measurement failed: this run says nothing about the finding"
        ),
    }
    out["verdict"] = {
        "public_search_returns_200_for_every_term": all_200,
        "public_search_body_identical_across_terms": identical,
        "database_discriminates_terms": discriminates,
        "records_filtered_by_term": filtered,
        # null, never false, when the measurement itself did not happen
        "finding_confirmed": bool(all_200 and identical and discriminates) if valid else None,
    }

    text = json.dumps(out, indent=2, ensure_ascii=False)
    write_report(args.out, text, args.force)
    print(text)

    return report_outcome(
        valid,
        bool(out["verdict"]["finding_confirmed"]),
        held=(
            "the public search returns the same page for every term while the "
            "registry's own endpoint discriminates."
        ),
        refuted=(
            "the measurement was valid and the finding did not hold on this run -- "
            "read the JSON before concluding anything."
        ),
        failed=(
            f"unreachable={unreachable or 'none'}; positive controls={controls}. "
            "Nothing here is evidence about the search."
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
