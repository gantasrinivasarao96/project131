import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.main import main


def test_cli_generates_json_report():
    repository = Path("data/sample/demo_project")

    with TemporaryDirectory() as temporary_directory:
        output_path = Path(temporary_directory) / "report.json"

        exit_code = main([
            str(repository),
            "--output",
            str(output_path),
        ])

        assert exit_code == 0
        assert output_path.is_file()

        report = json.loads(
            output_path.read_text(encoding="utf-8")
        )

        assert report["repository"] == "demo_project"
        assert report["python_file_count"] == 3
        assert "risk_baseline" in report
        assert report["risk_baseline"]["module_count"] == 3

    print("PASS: CLI generates a complete JSON analysis report.")


def test_cli_rejects_missing_repository():
    with TemporaryDirectory() as temporary_directory:
        missing_path = Path(temporary_directory) / "missing"

        try:
            main([str(missing_path)])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(
                "Expected CLI to reject a missing repository."
            )

    print("PASS: CLI rejects a missing repository.")


if __name__ == "__main__":
    test_cli_generates_json_report()
    test_cli_rejects_missing_repository()
