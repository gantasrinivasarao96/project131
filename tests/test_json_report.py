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

        # Repository information
        assert loaded_report["repository"] == "demo_project"
        assert loaded_report["python_file_count"] == 3

        # Dependency graph metrics
        graph_metrics = loaded_report["graph_metrics"]
        assert graph_metrics["node_count"] == 3
        assert graph_metrics["edge_count"] == 2

        # Code metrics
        code_metrics = loaded_report["code_metrics"]
        assert len(code_metrics) == 3

        # Static analysis
        static_analysis = loaded_report["static_analysis"]

        assert static_analysis["ruff"]["status"] == "completed"
        assert static_analysis["bandit"]["status"] == "completed"

        assert isinstance(static_analysis["ruff"]["findings"], list)
        assert isinstance(static_analysis["bandit"]["findings"], list)

        # Structural risk analysis
        structural_risk = loaded_report["structural_risk"]

        assert (
            structural_risk["method"]
            == "rule_based_structural_indicators"
        )
        assert isinstance(structural_risk["findings"], list)
        assert isinstance(structural_risk["finding_count"], int)
        assert (
            structural_risk["finding_count"]
            == len(structural_risk["findings"])
        )
        assert isinstance(structural_risk["thresholds"], dict)
        assert isinstance(structural_risk["interpretation"], str)

    print(
        "PASS: JSON report includes repository information, "
        "graph metrics, code metrics, static analysis, "
        "and structural risk analysis."
    )


if __name__ == "__main__":
    test_json_report()
