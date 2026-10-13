import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.analysis.repository_analyzer import analyze_repository
from src.reporting.json_report import save_json_report


def test_json_report():
    repository = Path("data/sample/demo_project")
    report = analyze_repository(repository)

    with TemporaryDirectory() as temporary_directory:
        output_path = Path(temporary_directory) / "report.json"

        saved_path = save_json_report(report, output_path)

        assert saved_path.exists()

        loaded_report = json.loads(
            saved_path.read_text(encoding="utf-8")
        )

        assert loaded_report["repository"] == "demo_project"
        assert loaded_report["python_file_count"] == 3
        assert loaded_report["graph_metrics"]["node_count"] == 3
        assert loaded_report["graph_metrics"]["edge_count"] == 2

    print("PASS: JSON report generation verified.")


if __name__ == "__main__":
    test_json_report()
