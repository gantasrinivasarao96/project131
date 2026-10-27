from pathlib import Path

from src.analysis.repository_analyzer import analyze_repository


def test_change_impact_in_repository_analyzer():
    root = Path("data/sample/demo_project")

    default_report = analyze_repository(root)
    assert default_report["change_impact"] is None

    report = analyze_repository(root, changed_module="database.py")
    impact = report["change_impact"]

    assert impact["changed_module"] == "database.py"
    assert impact["direct_dependents"] == ["auth.py"]
    assert impact["transitive_dependents"] == ["main.py"]
    assert impact["impact_count"] == 2

    print("PASS: Change-impact integration verified.")


def test_unknown_module_is_rejected_by_repository_analyzer():
    root = Path("data/sample/demo_project")

    try:
        analyze_repository(root, changed_module="missing.py")
    except ValueError as exc:
        assert "not present in graph" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown module")

    print("PASS: Unknown module rejected by repository analyzer.")


if __name__ == "__main__":
    test_change_impact_in_repository_analyzer()
    test_unknown_module_is_rejected_by_repository_analyzer()
