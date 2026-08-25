"""The figures are a byte-reproducible derivation, and this is what proves it.

Unlike matplotlib output in sister repositories, ``make_figure.py`` writes SVG
from the standard library alone: no fonts are rasterised, no version-dependent
backend runs. So the published SVGs must regenerate byte-identically, and their
SHA-256s are folded into ``artifact_root``. If this test ever fails, either the
generator lost determinism or the sealed figures were edited by hand.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIGURES = {
    "en": ROOT / "output" / "figures" / "fig1-defect1-chain.svg",
    "pt": ROOT / "output" / "figures" / "fig1-defect1-chain-pt.svg",
}


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_figure_regenerates_byte_identically(lang: str):
    """Regenerating the figure reproduces the sealed bytes exactly."""
    before = hashlib.sha256(FIGURES[lang].read_bytes()).hexdigest()
    subprocess.run(
        [sys.executable, str(ROOT / "code" / "make_figure.py"), "--lang", lang],
        check=True,
        cwd=ROOT,
        capture_output=True,
    )
    after = hashlib.sha256(FIGURES[lang].read_bytes()).hexdigest()
    assert after == before, f"{lang}: generator is no longer deterministic"


def test_provenance_chain_is_intact():
    """The sealed chain recomputes from the files on disk."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_chain.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CHAIN INTACT" in r.stdout
