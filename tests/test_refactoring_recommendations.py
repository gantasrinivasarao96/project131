from src.refactoring.recommendation_engine import (
    generate_refactoring_recommendations,
)


def test_refactoring_recommendations():
    graph = {
        "nodes": [
            "core.py",
            "api.py",
            "db.py",
            "worker.py",
            "large.py",
        ],
        "edges": [
            {"source": "api.py", "target": "core.py"},
            {"source": "db.py", "target": "core.py"},
            {"source": "worker.py", "target": "core.py"},
            {"source": "api.py", "target": "db.py"},
            {"source": "api.py", "target": "worker.py"},
            {"source": "api.py", "target": "large.py"},
        ],
    }

    code_metrics = [
        {"file": "large.py", "lines_of_code": 350},
        {"file": "core.py", "lines_of_code": 80},
        {"file": "api.py", "lines_of_code": 100},
        {"file": "db.py", "lines_of_code": 90},
        {"file": "worker.py", "lines_of_code": 70},
    ]

    result = generate_refactoring_recommendations(
        graph,
        code_metrics,
    )

    assert result["method"] == "rule_based_refactoring_recommendations"
    assert result["recommendation_count"] == 3

    types_by_file = {
        file: {
            item["type"]
            for item in result["recommendations"]
            if item["file"] == file
        }
        for file in graph["nodes"]
    }

    assert "high_fan_in" in types_by_file["core.py"]
    assert "high_fan_out" in types_by_file["api.py"]
    assert "large_source_file" in types_by_file["large.py"]

    assert all(
        item["recommendation"]
        for item in result["recommendations"]
    )

    print("PASS: Refactoring recommendation rules verified.")


def test_unknown_graph_node_raises_error():
    graph = {
        "nodes": ["main.py"],
        "edges": [
            {"source": "main.py", "target": "missing.py"},
        ],
    }

    try:
        generate_refactoring_recommendations(graph, [])
    except ValueError as exc:
        assert "unknown node" in str(exc)
    else:
        raise AssertionError("Expected ValueError for an unknown node")

    print("PASS: Invalid graph edge handled correctly.")


if __name__ == "__main__":
    test_refactoring_recommendations()
    test_unknown_graph_node_raises_error()
