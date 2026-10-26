from src.analysis.dependency_cycles import detect_dependency_cycles


def test_detects_circular_dependency():
    graph = {
        "nodes": ["a.py", "b.py", "c.py", "d.py"],
        "edges": [
            {"source": "a.py", "target": "b.py"},
            {"source": "b.py", "target": "c.py"},
            {"source": "c.py", "target": "a.py"},
            {"source": "c.py", "target": "d.py"},
        ],
    }

    result = detect_dependency_cycles(graph)

    assert result["cycle_group_count"] == 1
    assert result["cycles"][0]["modules"] == [
        "a.py", "b.py", "c.py"
    ]
    assert result["cycles"][0]["size"] == 3

    print("PASS: Circular dependency group detected.")


def test_acyclic_graph_has_no_cycles():
    graph = {
        "nodes": ["main.py", "auth.py", "database.py"],
        "edges": [
            {"source": "main.py", "target": "auth.py"},
            {"source": "auth.py", "target": "database.py"},
        ],
    }

    result = detect_dependency_cycles(graph)

    assert result["cycle_group_count"] == 0
    assert result["cycles"] == []

    print("PASS: Acyclic graph has no cycle groups.")


def test_detects_self_loop():
    graph = {
        "nodes": ["a.py"],
        "edges": [
            {"source": "a.py", "target": "a.py"},
        ],
    }

    result = detect_dependency_cycles(graph)

    assert result["cycle_group_count"] == 1
    assert result["cycles"][0]["type"] == "self_loop"

    print("PASS: Self-loop detected.")


def test_unknown_node_raises_error():
    graph = {
        "nodes": ["a.py"],
        "edges": [
            {"source": "a.py", "target": "missing.py"},
        ],
    }

    try:
        detect_dependency_cycles(graph)
    except ValueError as exc:
        assert "unknown node" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown node")

    print("PASS: Invalid graph edge handled correctly.")


if __name__ == "__main__":
    test_detects_circular_dependency()
    test_acyclic_graph_has_no_cycles()
    test_detects_self_loop()
    test_unknown_node_raises_error()
