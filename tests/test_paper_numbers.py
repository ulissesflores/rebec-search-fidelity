"""Every number the report publishes is an assertion here.

The gate in ``code/quality_checks.py`` resolves each load-bearing quantity from the
frozen JSONs under ``output/`` and ``data/derived/``, and requires it to appear in
BOTH editions. These tests drive that gate one check at a time, so a failure names
the gate that broke instead of returning a single red light.

Network-dependent gates (URL reachability, DOI resolution) live in
``test_citations_live.py``, marked ``live`` and deselected by default.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("gate", ROOT / "code" / "quality_checks.py")
gate = importlib.util.module_from_spec(_spec)
sys.modules["gate"] = gate
_spec.loader.exec_module(gate)


@pytest.fixture(autouse=True)
def _clean_failures():
    """Reset the gate's failure accumulator so each test reports only its own."""
    gate.failures.clear()
    yield


@pytest.fixture(scope="module")
def editions() -> tuple[str, str]:
    """Return the English and Portuguese editions as text."""
    return (gate.EN.read_text(encoding="utf-8"), gate.PT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sealed() -> dict:
    """Return the frozen JSONs the published numbers resolve from."""
    return gate.sealed()


def test_sealed_numbers_tie_to_frozen_data(editions, sealed):
    """Fifteen published quantities recompute from the sealed JSONs, in both languages.

    Twelve are the measurements of section 3; the other three are the re-measurement
    of 2026-09-04 published in section 5.1, held to the same rule.
    """
    rows = gate.numbers(*editions, sealed)
    assert not gate.failures, gate.failures
    assert len(rows) == 15


def test_recall_is_fourteen_of_seventeen(sealed):
    """The headline recall is set arithmetic over measured identifiers, not a quoted figure."""
    recall = sealed["recall"]
    assert len(recall["database"]) == 17
    assert len(recall["public_search"]) == 16
    assert len(set(recall["database"]) & set(recall["public_search"])) == 14
    assert sorted(recall["not_returned"]) == ["RBR-5vpyh4", "RBR-69pf3b", "RBR-7gstxs6"]
    assert sorted(recall["outside_database_filter"]) == ["RBR-7jmj48v", "RBR-84nk5q6"]


def test_public_search_body_is_identical_across_all_six_terms(sealed):
    """Defect 2: one body, one SHA-256, for six different queries."""
    bodies = sealed["search"]["public_search"]
    assert len(bodies) == 6
    assert len({b["sha256"] for b in bodies.values()}) == 1
    assert len({b["bytes"] for b in bodies.values()}) == 1
    assert {b["http"] for b in bodies.values()} == {200}


def test_database_discriminates_the_same_six_terms(sealed):
    """The control arm: the registry's own endpoint answers each term differently."""
    assert sealed["search"]["verdict"]["records_filtered_by_term"] == {
        "dengue": 17,
        "diabetes": 1452,
        "prion": 1,
        "Creutzfeldt": 0,
        "Jakob": 0,
        "priônica": 0,
    }
    assert sealed["search"]["registry_database"]["dengue"]["recordsTotal"] == 9629


def test_unrecognised_parameter_returns_the_whole_database(sealed):
    """Arm 4: passing `q=` raises no error and silently returns every record."""
    trap = sealed["search"]["unrecognised_parameter"]
    assert trap["parameter"] == "q"
    assert trap["returns_whole_database"] is True
    assert trap["recordsFiltered"] == trap["recordsTotal"] == 9629


def test_archive_captures_are_byte_identical(sealed):
    """Duration: three different queries, two minutes apart, one digest."""
    captures = sealed["archive"]["captures_2025_09_23"]
    assert len(captures) == 3
    assert len({c["sha256"] for c in captures}) == 1
    assert all(c["term_present_in_html"] is False for c in captures)


def test_downstream_counts_are_sealed(sealed):
    """The three co-occurrence counts of section 4.1 come from a sealed file."""
    counts = sealed["downstream"]["counts"]
    assert counts["ReBEC"] == 2798
    assert counts['"Brazilian Registry of Clinical Trials"'] == 1234
    assert counts['"ensaiosclinicos.gov.br"'] == 494


def test_artefact_hash_table_matches_the_files_on_disk(editions):
    """Section 6 publishes SHA-256s; they are recomputed from the bytes here."""
    gate.hashes(*editions)
    assert not gate.failures, gate.failures


def test_references_are_complete_and_ordered(editions):
    """Every [n] has an entry, every entry is cited, numbering is a run of 1..N."""
    en, pt = editions
    english = gate.references(en, "EN", "References")
    portuguese = gate.references(pt, "PT", "Referências")
    assert not gate.failures, gate.failures
    assert english["entries"] == portuguese["entries"] == 21
    assert english["cited"] == portuguese["cited"] == list(range(1, 22))


def test_no_placeholders_survive(editions):
    """A deposit carries no TODO/TBD/XXX/FIXME/<...>."""
    en, pt = editions
    assert gate.placeholders(en, "EN") == 0
    assert gate.placeholders(pt, "PT") == 0
    assert not gate.failures, gate.failures


def test_section_skeletons_match_across_editions(editions):
    """The translation is integral: same sections, same numbering."""
    result = gate.parity(*editions)
    assert not gate.failures, gate.failures
    assert result["identical"]


def test_density_clears_the_frozen_thresholds(editions):
    """TDI, filler ratio and info density, against the calibration frozen before scoring."""
    concepts = gate.load_concepts()
    for lang, text in zip(("en", "pt"), editions, strict=True):
        measured = gate.density(text, concepts, lang)
        assert measured["tdi"] >= 3.0, (lang, measured)
        assert measured["filler_ratio"] < 0.12, (lang, measured)
        assert measured["info_density"] >= 0.15, (lang, measured)
    assert not gate.failures, gate.failures


def test_human_observed_quantities_are_traceable(editions):
    """The three browser-observed numbers are not recomputable, so they are traced."""
    rows = gate.attested(*editions)
    assert not gate.failures, gate.failures
    assert all(row["traced"] for row in rows)


def test_calibration_hash_matches_the_recorded_one():
    """The audit cites the calibration by hash; that hash must still be the file's."""
    recorded = json.loads(
        (ROOT / "docs" / "paper" / "quality-checks-report.json").read_text(encoding="utf-8")
    )["calibration"]["sha256"]
    assert hashlib.sha256(gate.CALIBRATION.read_bytes()).hexdigest() == recorded
