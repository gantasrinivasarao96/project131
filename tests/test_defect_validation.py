import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from src.prediction.defect_validation import inspect_commit


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def create_repository(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.name", "Test User")
    run_git(root, "config", "user.email", "test@example.com")


def commit_files(root: Path, message: str, files: dict) -> str:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    run_git(root, "add", ".")
    run_git(root, "commit", "-m", message)

    return run_git(root, "rev-parse", "HEAD")


def test_inspects_commit_metadata_and_patch():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit = commit_files(
            root,
            "Update application behavior",
            {"src/app.py": "value = 2\n"},
        )

        result = inspect_commit(root, commit)

        assert result["commit_hash"] == commit
        assert result["message"] == "Update application behavior"
        assert result["changed_file_count"] == 1
        assert result["category_counts"] == {"production": 1}
        assert result["patch_available"] is True
        assert result["review_status"] == "uncertain"
        assert result["label_source"] == "manual_reviewer"

        item = result["changed_files"][0]
        assert item["path"] == "src/app.py"
        assert item["category"] == "production"
        assert item["line_changes"]["added"] == 1

    print("PASS: Commit metadata and patch inspected.")


def test_classifies_changed_file_categories():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit = commit_files(
            root,
            "Update project files",
            {
                "src/app.py": "value = 1\n",
                "tests/test_app.py": "assert True\n",
                ".github/workflows/ci.yml": "name: CI\n",
                "requirements.txt": "requests\n",
                "README.md": "Project documentation\n",
                "assets/data.json": "{}\n",
            },
        )

        result = inspect_commit(root, commit)

        assert result["category_counts"] == {
            "production": 1,
            "test": 1,
            "ci_cd": 1,
            "configuration_or_dependency": 1,
            "documentation": 1,
            "other": 1,
        }

    print("PASS: Changed file categories classified.")


def test_records_added_and_deleted_lines():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(
            root,
            "Initial source",
            {"src/app.py": "value = 1\n"},
        )

        commit = commit_files(
            root,
            "Update source",
            {"src/app.py": "value = 2\nvalue = 3\n"},
        )

        result = inspect_commit(root, commit)
        changes = result["changed_files"][0]["line_changes"]

        assert changes["added"] == 2
        assert changes["deleted"] == 1
        assert changes["binary"] is False

    print("PASS: Added and deleted line counts recorded.")


def test_invalid_review_status_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit = commit_files(
            root,
            "Initial commit",
            {"app.py": "value = 1\n"},
        )

        try:
            inspect_commit(root, commit, review_status="automatic")
        except ValueError:
            pass
        else:
            raise AssertionError("Expected invalid review status to fail")

    print("PASS: Invalid review status rejected.")


def test_invalid_commit_hash_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        try:
            inspect_commit(root, "invalid-commit-hash")
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected invalid commit hash to fail")

    print("PASS: Invalid commit hash rejected.")


def test_non_git_directory_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)

        try:
            inspect_commit(root, "invalid-commit-hash")
        except ValueError:
            pass
        else:
            raise AssertionError("Expected non-Git directory to fail")

    print("PASS: Non-Git directory rejected.")


if __name__ == "__main__":
    test_inspects_commit_metadata_and_patch()
    test_classifies_changed_file_categories()
    test_records_added_and_deleted_lines()
    test_invalid_review_status_is_rejected()
    test_invalid_commit_hash_is_rejected()
    test_non_git_directory_is_rejected()


def test_initial_commit_files_are_detected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit = commit_files(
            root,
            "Initial project",
            {"src/app.py": "value = 1\n"},
        )

        result = inspect_commit(root, commit)

        assert result["changed_file_count"] == 1
        assert result["changed_files"][0]["path"] == "src/app.py"
        assert result["changed_files"][0]["status"] == "A"

    print("PASS: Initial commit files detected.")


def test_merge_commit_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(root, "Initial commit", {"app.py": "value = 1\n"})

        run_git(root, "branch", "feature")
        run_git(root, "checkout", "feature")
        commit_files(root, "Feature change", {"feature.py": "value = 2\n"})

        run_git(root, "checkout", "master")
        commit_files(root, "Main change", {"main.py": "value = 3\n"})

        run_git(root, "merge", "--no-ff", "feature", "-m", "Merge feature")

        merge_commit = run_git(root, "rev-parse", "HEAD")

        try:
            inspect_commit(root, merge_commit)
        except ValueError as error:
            assert "Merge commits are not supported" in str(error)
        else:
            raise AssertionError("Expected merge commit to be rejected")

    print("PASS: Merge commit rejected.")


def test_binary_file_changes_are_handled():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        binary_path = root / "assets" / "image.bin"
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.write_bytes(b"\x00\x01\x02\x03")

        run_git(root, "add", ".")
        run_git(root, "commit", "-m", "Add binary file")
        commit = run_git(root, "rev-parse", "HEAD")

        result = inspect_commit(root, commit)

        item = result["changed_files"][0]
        assert item["path"] == "assets/image.bin"
        assert item["line_changes"]["binary"] is True
        assert item["line_changes"]["added"] is None
        assert item["line_changes"]["deleted"] is None

    print("PASS: Binary file changes handled correctly.")
