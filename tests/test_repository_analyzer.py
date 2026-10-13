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

    print("PASS: Repository analysis verified.")


if __name__ == "__main__":
    test_sample_repository_analysis()
