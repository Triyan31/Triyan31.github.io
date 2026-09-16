import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "review_academic.py"
# review_academic is normally executed from scripts/, where sync_academic is
# importable as a sibling module. Reproduce that runtime import path in tests.
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("review_academic", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def candidate():
    return {"doi": "10.1234/example", "title": "Example", "source": "test", "authors": ["Triyan A L"]}


def test_build_decision_records_authenticated_actor():
    result = review.build_decision(candidate(), "10.1234/example", "reject", "Triyan31", "2026-09-16T00:00:00+00:00")
    assert result["decided_by"] == "Triyan31"
    assert result["decision"] == "reject"


def test_invalid_actor_fails_closed():
    try:
        review.normalize_actor("bad actor!")
    except SystemExit:
        pass
    else:
        raise AssertionError("invalid actor must fail closed")


def test_decision_storage_is_append_only():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'decisions.setdefault("decisions", []).append(decision)' in source
    assert '[d for d in decisions.get("decisions", []) if doi_norm(d.get("doi")) != doi]' not in source


def test_repeated_doi_history_can_be_preserved():
    history = []
    first = review.build_decision(candidate(), "10.1234/example", "reject", "Triyan31", "2026-09-16T00:00:00+00:00")
    second = review.build_decision(candidate(), "10.1234/example", "approve", "Triyan31", "2026-09-16T01:00:00+00:00", "https://doi.org/10.1234/example")
    history.append(first)
    history.append(second)
    assert len(history) == 2
    assert [item["decision"] for item in history] == ["reject", "approve"]
    assert history[-1]["decided_at"] > history[0]["decided_at"]
