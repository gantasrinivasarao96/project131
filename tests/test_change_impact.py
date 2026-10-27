from src.analysis.change_impact import analyze_change_impact


def test_direct_and_transitive_impact():
    graph = {
        "nodes": [
            "main.py",
            "auth.py",
            "database.py",
            "report.py",
            "utils.py",
        ],
        "edges": [
            {"source": "main.py", "target": "auth.py"},
            {"source": "auth.py", "target": "database.py"},
            {"source": "report.py", "target": "database.py"},
            {"source": "main.py", "target": "utils.py"},
        ],
    }

    result = analyze_change_impact(graph, "database.py")

    assert result["direct_dependents"] == ["auth.py", "report.py"]
    assert result["transitive_dependents"] == ["main.py"]
    assert result["impacted_modules"] == [
        "auth.py", "main.py", "report.py"
    ]
    assert result["impact_count"] == 3

    print("PASS: Direct and transitive change impact verified.")


def test_cycle_does_not_cause_infinite_traversal():
    graph = {
        "nodes": ["a.py", "b.py", "c.py"],
        "edges": [
            {"source": "a.py", "target": "b.py"},
            {"source": "b.py", "target": "a.py"},
            {"source": "c.py", "target": "b.py"},
        ],
    }

    result = analyze_change_impact(graph, "a.py")

    assert result["direct_dependents"] == ["b.py"]
    assert result["transitive_dependents"] == ["c.py"]
    assert result["impact_count"] == 2

    print("PASS: Cyclic graph traversal terminates correctly.")


def test_unknown_changed_module_raises_error():
    graph = {
        "nodes": ["main.py"],
        "edges": [],
    }

    try:
        analyze_change_impact(graph, "missing.py")
    except ValueError as exc:
        assert "not present in graph" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown module")

    print("PASS: Unknown changed module rejected.")


if __name__ == "__main__":
    test_direct_and_transitive_impact()
    test_cycle_does_not_cause_infinite_traversal()
    test_unknown_changed_module_raises_error()
