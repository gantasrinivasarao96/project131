from src.prediction.risk_baseline import calculate_risk_baseline


def test_scores_modules_using_explicit_evidence():
    graph = {
        "nodes": ["core.py", "api.py", "db.py", "worker.py"],
        "edges": [
            {"source": "api.py", "target": "core.py"},
            {"source": "db.py", "target": "core.py"},
            {"source": "worker.py", "target": "core.py"},
            {"source": "api.py", "target": "db.py"},
            {"source": "api.py", "target": "worker.py"},
            {"source": "api.py", "target": "core.py"},
        ],
    }

    metrics = [
        {"file": "core.py", "lines_of_code": 350},
        {"file": "api.py", "lines_of_code": 100},
        {"file": "db.py", "lines_of_code": 80},
        {"file": "worker.py", "lines_of_code": 60},
    ]

    history = {
        "status": "completed",
        "cochange_pairs": [
            {
                "file_a": "core.py",
                "file_b": "api.py",
                "cochange_count": 4,
            }
        ],
    }

    result = calculate_risk_baseline(graph, metrics, history)
    by_file = {item["file"]: item for item in result["results"]}

    assert by_file["core.py"]["review_score"] == 3
    assert by_file["core.py"]["review_priority"] == "high"
    assert by_file["api.py"]["review_score"] == 2
    assert by_file["db.py"]["review_score"] == 0
    assert result["module_count"] == 4

    assert (
        result["label"]
        == "review_priority_not_defect_probability"
    )

    print("PASS: Baseline scoring and priorities verified.")


def test_baseline_works_without_git_history():
    graph = {
        "nodes": ["main.py"],
        "edges": [],
    }

    result = calculate_risk_baseline(
        graph,
        [{"file": "main.py", "lines_of_code": 20}],
        {"status": "unavailable", "reason": "No Git history"},
    )

    assert result["results"][0]["review_score"] == 0
    assert result["results"][0]["review_priority"] == "low"

    print("PASS: Baseline works without Git history.")


def test_unknown_graph_node_is_rejected():
    graph = {
        "nodes": ["main.py"],
        "edges": [
            {"source": "main.py", "target": "missing.py"},
        ],
    }

    try:
        calculate_risk_baseline(graph, [])
    except ValueError as exc:
        assert "unknown node" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown graph node")

    print("PASS: Invalid graph edge rejected.")


if __name__ == "__main__":
    test_scores_modules_using_explicit_evidence()
    test_baseline_works_without_git_history()
    test_unknown_graph_node_is_rejected()
