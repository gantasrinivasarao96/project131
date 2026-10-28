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




def test_cli_analyzes_zip_archive():
    import zipfile

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "demo.zip"
        output_path = root / "report.json"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.write("data/sample/demo_project/main.py", "demo/main.py")
            archive.write("data/sample/demo_project/auth.py", "demo/auth.py")
            archive.write("data/sample/demo_project/database.py", "demo/database.py")

        exit_code = main([
            str(archive_path),
            "--output",
            str(output_path),
        ])

        assert exit_code == 0
        assert output_path.is_file()

        report = json.loads(output_path.read_text(encoding="utf-8"))
        assert report["python_file_count"] == 3

    print("PASS: CLI analyzes ZIP archives.")


def test_cli_rejects_zip_without_python_files():
    import zipfile

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "empty-source.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("README.txt", "No Python source here.")

        exit_code = main([str(archive_path), "--output", str(root / "report.json")])
        assert exit_code == 1

    print("PASS: CLI rejects ZIP archives without Python source.")




def test_cli_cleans_up_zip_workspace_after_analysis_failure():
    import zipfile
    from unittest.mock import patch

    from src import main as main_module

    captured = {}

    original_temporary_directory = main_module.tempfile.TemporaryDirectory

    def tracked_temporary_directory(*args, **kwargs):
        workspace = original_temporary_directory(*args, **kwargs)
        captured["path"] = Path(workspace.name)
        return workspace

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "demo.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("demo/main.py", "print('hello')")

        with patch.object(
            main_module.tempfile,
            "TemporaryDirectory",
            side_effect=tracked_temporary_directory,
        ), patch.object(
            main_module,
            "analyze_repository",
            side_effect=RuntimeError("simulated analysis failure"),
        ):
            exit_code = main_module.main([
                str(archive_path),
                "--output",
                str(root / "report.json"),
            ])

        assert exit_code == 1
        assert "path" in captured
        assert not captured["path"].exists()

    print("PASS: ZIP workspace cleaned after analysis failure.")


if __name__ == "__main__":
    test_cli_generates_json_report()
    test_cli_rejects_missing_repository()
    test_cli_analyzes_zip_archive()
    test_cli_rejects_zip_without_python_files()
    test_cli_cleans_up_zip_workspace_after_analysis_failure()
