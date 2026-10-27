from pathlib import Path

from src.analysis.repository_analyzer import analyze_repository


def test_sample_repository_handles_unavailable_git_history():
    report = analyze_repository(Path("data/sample/demo_project"))

    assert report["git_history"]["status"] == "unavailable"
    assert report["python_file_count"] == 3
    assert report["graph_metrics"]["node_count"] == 3

    print("PASS: Git history availability handled correctly.")


if __name__ == "__main__":
    test_sample_repository_handles_unavailable_git_history()
