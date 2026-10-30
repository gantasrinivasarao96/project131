import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from src.analysis.git_history import analyze_git_history


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


def test_detects_repeated_cochanges():
    with TemporaryDirectory() as directory:
        root = Path(directory)

        run_git(root, "init")
        run_git(root, "config", "user.name", "Test User")
        run_git(root, "config", "user.email", "test@example.com")

        commit_files(
            root,
            "initial files",
            {"a.py": "value = 1\n", "b.py": "value = 1\n"},
        )
        commit_files(
            root,
            "update both files",
            {"a.py": "value = 2\n", "b.py": "value = 2\n"},
        )
        commit_files(
            root,
            "update both files again",
            {"a.py": "value = 3\n", "b.py": "value = 3\n"},
        )

        result = analyze_git_history(root, min_cochange_count=2)

        assert result["commit_count"] == 3
        assert result["cochange_pair_count"] == 1
        assert result["cochange_pairs"] == [
            {
                "file_a": "a.py",
                "file_b": "b.py",
                "cochange_count": 3,
            }
        ]

    print("PASS: Repeated co-changes counted correctly.")


def test_minimum_threshold_filters_pairs():
    with TemporaryDirectory() as directory:
        root = Path(directory)

        run_git(root, "init")
        run_git(root, "config", "user.name", "Test User")
        run_git(root, "config", "user.email", "test@example.com")

        commit_files(
            root,
            "initial files",
            {"a.py": "value = 1\n", "b.py": "value = 1\n"},
        )
        commit_files(
            root,
            "change only a",
            {"a.py": "value = 2\n"},
        )

        result = analyze_git_history(root, min_cochange_count=2)

        assert result["cochange_pair_count"] == 0
        assert result["cochange_pairs"] == []

    print("PASS: Co-change threshold filters pairs.")


def test_invalid_arguments_are_rejected():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        run_git(root, "init")

        try:
            analyze_git_history(root, max_commits=0)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected invalid max_commits to fail")

        try:
            analyze_git_history(root, min_cochange_count=0)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Expected invalid min_cochange_count to fail"
            )

    print("PASS: Invalid history-analysis arguments rejected.")


if __name__ == "__main__":
    test_detects_repeated_cochanges()
    test_minimum_threshold_filters_pairs()
    test_invalid_arguments_are_rejected()
