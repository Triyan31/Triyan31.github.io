import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_academic.py"
spec = importlib.util.spec_from_file_location("sync_academic", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def test_latest_decision_for_same_doi_wins_without_deleting_history():
    history = [
        {"doi": "10.1234/example", "decision": "reject", "decided_at": "2026-09-16T00:00:00+00:00", "decided_by": "Triyan31"},
        {"doi": "https://doi.org/10.1234/example", "decision": "approve", "decided_at": "2026-09-16T01:00:00+00:00", "decided_by": "Triyan31"},
    ]
    latest = sync.latest_decisions_by_doi(history)
    assert len(history) == 2
    assert latest["10.1234/example"]["decision"] == "approve"
    assert latest["10.1234/example"]["decided_at"] == "2026-09-16T01:00:00+00:00"


def test_latest_reject_for_same_doi_is_current_suppression_state():
    history = [
        {"doi": "doi:10.1234/example", "decision": "approve", "decided_at": "2026-09-16T00:00:00+00:00"},
        {"doi": "10.1234/example", "decision": "reject", "decided_at": "2026-09-16T01:00:00+00:00", "decided_by": "Triyan31"},
    ]
    latest = sync.latest_decisions_by_doi(history)
    assert latest["10.1234/example"]["decision"] == "reject"
    assert latest["10.1234/example"]["decided_by"] == "Triyan31"


def test_records_without_doi_do_not_become_current_state():
    history = [{"decision": "reject"}, {"doi": "", "decision": "approve"}]
    assert sync.latest_decisions_by_doi(history) == {}
