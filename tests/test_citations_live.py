"""Live checks on the cited sources. Deselected by default (marked ``live``).

Run with ``python -m pytest tests -m live``. They are excluded from the default run
and from CI on purpose: a cited journal being briefly unreachable is not a defect in
this artifact, and a replication must not depend on someone else's uptime. The
reachability recorded at deposit time is in ``docs/paper/quality-checks-report.json``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("gate", ROOT / "code" / "quality_checks.py")
gate = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("gate", gate)
_spec.loader.exec_module(gate)

pytestmark = pytest.mark.live


def test_cited_urls_and_dois_resolve():
    """Every cited URL answers 2xx/3xx and every DOI is known to Crossref."""
    gate.failures.clear()
    result = gate.network(gate.EN.read_text(encoding="utf-8"), gate.PT.read_text(encoding="utf-8"))
    assert not gate.failures, gate.failures
    assert len(result["urls"]) >= 4
    assert len(result["dois"]) >= 9
