#!/usr/bin/env python3
"""Measure whether defect 1 still holds: the search box's target and the certificate.

Section 5 of the report promises that this finding expires the day the registry
repairs it. That promise was only kept for defects 2 and 3: the other two
instruments never touch TLS, so defect 1 could have been repaired without any
released instrument noticing. This file closes that gap.

Defect 1 is a chain of two machine-checkable links, and it survives only while
BOTH hold:

1. **The widget still points at the ``www`` host over ``http``.** The registry's
   search box is a Google Custom Search element whose configuration
   (``cse.js?cx=...``) names exactly one URL for this site.
2. **The certificate still does not cover that host.** A TLS client that checks
   the presented identity against the certificate (RFC 9525) refuses
   ``www.ensaiosclinicos.gov.br``, because the certificate carries a single
   ``subjectAltName`` for the bare domain.

Repairing either link repairs the defect: re-point the widget at the canonical
host, or issue a certificate that covers ``www``. Both are visible here.

The certificate is read with hostname verification left ON, exactly as a browser
does it. The refusal IS the measurement -- we do not disable the check and then
reason about what a browser would have done.

Exit codes (see ``code/measurement.py``): 0 defect 1 still holds, 1 it does not
(at least one link repaired), 2 the measurement could not be made.

Usage
-----
``python3 code/measure_defect1_tls.py [--out output/reruns/defect1-tls.json]``
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import sys
import time
import urllib.request

from measurement import add_out_argument, report_outcome, write_report

CANONICAL_HOST = "ensaiosclinicos.gov.br"
WWW_HOST = "www.ensaiosclinicos.gov.br"
CSE_CONFIG = "https://cse.google.com/cse.js?cx=ad5f3224a2a0fa826"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
TIMEOUT = 30


def widget_targets() -> list[str]:
    """Every URL for this site that the published widget configuration names."""
    request = urllib.request.Request(CSE_CONFIG, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        body = response.read().decode("utf-8", "replace")
    return sorted(set(re.findall(r"https?://[\w.-]*ensaiosclinicos\.gov\.br[^\s\"'\\]*", body)))


def verified_handshake(host: str) -> tuple[bool, str | None, list[str]]:
    """Open TLS to ``host`` as a browser would, verifying the presented identity.

    Returns
    -------
    tuple[bool, str | None, list[str]]
        Whether verification succeeded, the verification error if it did not, and
        the ``subjectAltName`` entries when the certificate could be read.
    """
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as raw:
            with context.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert() or {}
                names = [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"]
                return True, None, sorted(names)
    except ssl.SSLCertVerificationError as exc:
        return False, f"{type(exc).__name__}: {exc.verify_message or exc}", []


def main() -> int:
    """Measure both links of defect 1, write the report, return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_out_argument(parser, "output/reruns/defect1-tls.json")
    args = parser.parse_args()

    error: str | None = None
    targets: list[str] = []
    www_verified: bool | None = None
    www_error: str | None = None
    canonical_sans: list[str] = []
    try:
        targets = widget_targets()
        www_verified, www_error, _ = verified_handshake(WWW_HOST)
        canonical_ok, _, canonical_sans = verified_handshake(CANONICAL_HOST)
        if not canonical_ok:
            # The canonical host failing verification is a different world from
            # the one this report measured; refuse to report a verdict about it.
            error = "the canonical host itself no longer verifies -- re-measure by hand"
    except Exception as exc:  # DNS, connection refused, timeout, unreadable config
        error = f"{type(exc).__name__}: {exc}"

    valid = error is None and www_verified is not None
    widget_points_at_www = any(t.startswith(f"http://{WWW_HOST}") for t in targets)
    certificate_covers_www = bool(www_verified)
    holds = valid and widget_points_at_www and not certificate_covers_www

    report = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "widget_configuration": {
            "source": CSE_CONFIG,
            "urls_for_this_site": targets,
            "points_at_www_over_http": widget_points_at_www,
        },
        "certificate": {
            "host_checked": WWW_HOST,
            "verification_succeeded": www_verified,
            "verification_error": www_error,
            "canonical_host_subject_alt_names": canonical_sans,
            "covers_www": certificate_covers_www,
        },
        "measurement": {"valid": valid, "error": error},
        "verdict": {
            "link_1_widget_points_at_uncovered_host": widget_points_at_www if valid else None,
            "link_2_certificate_does_not_cover_it": (not certificate_covers_www) if valid else None,
            # null, never false, when the measurement did not happen
            "defect_1_still_holds": holds if valid else None,
        },
    }
    write_report(args.out, json.dumps(report, ensure_ascii=False, indent=2), args.force)
    print(json.dumps(report["verdict"], ensure_ascii=False, indent=2))

    return report_outcome(
        valid,
        holds,
        held=(
            f"the widget still sends visitors to http://{WWW_HOST} and the certificate "
            f"still does not cover it ({canonical_sans})."
        ),
        refuted=(
            "at least one link is repaired -- "
            f"widget points at www: {widget_points_at_www}; "
            f"certificate covers www: {certificate_covers_www}."
        ),
        failed=f"{error or 'the TLS handshake produced no verdict'}.",
    )


if __name__ == "__main__":
    sys.exit(main())
