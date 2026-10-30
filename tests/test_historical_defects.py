import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from src.prediction.historical_defects import extract_historical_commits


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def commit_files(root: Path, message: str, files: dict) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    run_git(root, "add", ".")
    run_git(root, "commit", "-m", message)


def create_repository(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.name", "Test User")
    run_git(root, "config", "user.email", "test@example.com")


def test_extracts_commit_metadata_and_file_categories():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(
            root,
            "Fix parser behavior",
            {
                "src/parser.py": "value = 1\n",
                "tests/test_parser.py": "assert True\n",
                "README.md": "Test repository\n",
            },
        )

        result = extract_historical_commits(root)

        assert result["commit_count"] == 1
        assert result["candidate_defect_fix_count"] == 1

        commit = result["commits"][0]

        assert commit["message"] == "Fix parser behavior"
        assert commit["candidate_defect_fix"] is True
        assert commit["label"] == "needs_review"
        assert commit["production_files"] == ["src/parser.py"]
        assert commit["test_files"] == ["tests/test_parser.py"]
        assert "README.md" in commit["changed_files"]
        assert (
            commit["labeling_method"]
            == "commit_message_keyword_candidate"
        )

    print("PASS: Commit metadata and file categories extracted.")


def test_non_fix_commit_remains_unlabeled():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(
            root,
            "Add parser documentation",
            {"README.md": "Parser documentation\n"},
        )

        result = extract_historical_commits(root)

        assert result["commit_count"] == 1
        assert result["candidate_defect_fix_count"] == 0
        assert result["unlabeled_commit_count"] == 1
        assert result["commits"][0]["label"] == "unlabeled"

    print("PASS: Non-fix commits remain unlabeled.")


def test_max_commits_limits_extraction():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(root, "Initial commit", {"a.py": "value = 1\n"})
        commit_files(root, "Fix parser", {"a.py": "value = 2\n"})

        result = extract_historical_commits(root, max_commits=1)

        assert result["commit_count"] == 1
        assert result["commits"][0]["message"] == "Fix parser"

    print("PASS: Maximum commit limit is respected.")


def test_invalid_max_commits_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        try:
            extract_historical_commits(root, max_commits=0)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected max_commits=0 to fail")

    print("PASS: Invalid maximum commit count rejected.")


def test_non_git_directory_is_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)

        try:
            extract_historical_commits(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected non-Git directory to fail")

    print("PASS: Non-Git directory rejected.")


def test_empty_repository_returns_no_commits():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        result = extract_historical_commits(root)

        assert result["commit_count"] == 0
        assert result["candidate_defect_fix_count"] == 0
        assert result["unlabeled_commit_count"] == 0
        assert result["commits"] == []

    print("PASS: Empty repository handled correctly.")


if __name__ == "__main__":
    test_extracts_commit_metadata_and_file_categories()
    test_non_fix_commit_remains_unlabeled()
    test_max_commits_limits_extraction()
    test_invalid_max_commits_is_rejected()
    test_non_git_directory_is_rejected()
    test_empty_repository_returns_no_commits()


def test_keyword_match_is_only_a_candidate():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        create_repository(root)

        commit_files(
            root,
            "Discuss bug reporting documentation",
            {"README.md": "This project explains bug reporting.\n"},
        )

        result = extract_historical_commits(root)
        commit = result["commits"][0]

        assert commit["candidate_defect_fix"] is True
        assert commit["label"] == "needs_review"
        assert commit["label"] != "confirmed"
        assert commit["labeling_method"] == (
            "commit_message_keyword_candidate"
        )

    print("PASS: Keyword matches remain unconfirmed candidates.")
