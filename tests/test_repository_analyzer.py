from pathlib import Path

from src.analysis.repository_analyzer import analyze_repository


def test_sample_repository_analysis():
    result = analyze_repository(
        Path("data/sample/demo_project")
    )

    assert result["repository"] == "demo_project"
    assert result["python_file_count"] == 3
    assert result["graph_metrics"]["node_count"] == 3
    assert result["graph_metrics"]["edge_count"] == 2
    assert len(result["code_metrics"]) == 3
    assert result["parse_errors"] == []

    assert "risk_baseline" in result

    baseline = result["risk_baseline"]
    assert (
        baseline["method"]
        == "transparent_rule_based_review_baseline"
    )
    assert (
        baseline["label"]
        == "review_priority_not_defect_probability"
    )
    assert baseline["module_count"] == 3
    assert len(baseline["results"]) == 3

    for item in baseline["results"]:
        assert item["review_priority"] in {
            "low",
            "medium",
            "high",
        }
        assert 0 <= item["review_score"] <= 4
        assert isinstance(item["evidence"], list)

    print(
        "PASS: Repository analysis includes risk baseline "
        "with valid scores and priorities."
    )


if __name__ == "__main__":
    test_sample_repository_analysis()
