#!/usr/bin/env python3
"""The discipline the instruments of this report share, in one place.

Two rules live here because both were violated by the instruments before they
were written down, and a rule that exists in three copies is a rule that will
drift in two of them.

**Rule 1 -- a failed measurement is not a refuted finding.** This report argues
(§2.1) that without a positive control an empty result cannot distinguish "there
is nothing" from "the search did not run". An instrument that returns the same
exit code for "the registry repaired its search" and "the network was down"
commits exactly that confusion about itself. Hence three exit codes, not two.

**Rule 2 -- an instrument must not overwrite the artefact it was sealed as.**
The report ships hashes of the JSONs under ``output/``. If re-running an
instrument writes over them by default, following the report's own instructions
breaks the report's own provenance chain. Reruns therefore land in
``output/reruns/`` and an existing file is never silently replaced.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: The finding still held on this run.
EXIT_FINDING_HOLDS = 0
#: The measurement ran, was valid, and the finding did NOT hold -- possibly repaired.
EXIT_FINDING_REFUTED = 1
#: The measurement could not be made. This says nothing at all about the finding.
EXIT_MEASUREMENT_FAILED = 2


def add_out_argument(parser, default: str) -> None:
    """Add ``--out``/``--force``, defaulting away from any sealed artefact.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The instrument's parser.
    default : str
        Path under ``output/reruns/``. Never a path the report publishes a hash of.
    """
    parser.add_argument(
        "--out", default=default, help=f"where to write the report (default: {default})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite --out if it already exists (refused by default)",
    )


def write_report(path: str, text: str, force: bool) -> None:
    """Write ``text`` to ``path``, refusing to replace an existing file.

    Raises
    ------
    SystemExit
        With ``EXIT_MEASUREMENT_FAILED`` if the target exists and ``force`` is
        not set. Refusing is the point: the caller has aimed an instrument at a
        file that is somebody's evidence.
    """
    target = Path(path)
    if target.exists() and not force:
        print(
            f"refusing to overwrite {target} -- it may be sealed evidence.\n"
            f"Pass --out with another path, or --force if you meant it.",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_MEASUREMENT_FAILED)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def report_outcome(valid: bool, confirmed: bool, held: str, refuted: str, failed: str) -> int:
    """Turn a validity flag and a verdict into one of the three exit codes.

    Parameters
    ----------
    valid : bool
        Whether the measurement itself can be trusted (requests completed, the
        positive control behaved).
    confirmed : bool
        The finding's verdict. Only meaningful when ``valid``.
    held, refuted, failed : str
        The sentence to print in each case.
    """
    if not valid:
        print(f"\nMEASUREMENT FAILED: {failed}", file=sys.stderr)
        return EXIT_MEASUREMENT_FAILED
    if confirmed:
        print(f"\nFINDING CONFIRMED: {held}", file=sys.stderr)
        return EXIT_FINDING_HOLDS
    print(f"\nFINDING NOT CONFIRMED: {refuted}", file=sys.stderr)
    return EXIT_FINDING_REFUTED
