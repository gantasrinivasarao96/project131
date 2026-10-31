import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.prediction.prefix_features import extract_prefix_features


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


class TestPrefixFeatures(unittest.TestCase):

    def test_extracts_features_from_parent_snapshot(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)

            initial_source = (
                "import os\n"
                "def first():\n"
                "    return 1\n"
                "def second():\n"
                "    return 2\n"
            )

            commit_files(
                root,
                "Initial source",
                {"src/app.py": initial_source},
            )

            fixing_commit = commit_files(
                root,
                "Fix application",
                {"src/app.py": "value = 1\n"},
            )

            result = extract_prefix_features(root, fixing_commit)

            self.assertEqual(result["fixing_commit"], fixing_commit)
            self.assertEqual(result["changed_python_file_count"], 1)
            self.assertEqual(result["feature_file_count"], 1)

            feature = result["file_features"][0]

            self.assertEqual(feature["file"], "src/app.py")
            self.assertEqual(feature["code_metrics"]["lines_of_code"], 5)
            self.assertEqual(feature["code_metrics"]["function_count"], 2)
            self.assertEqual(feature["code_metrics"]["import_count"], 1)

    def test_root_commit_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)

            root_commit = commit_files(
                root,
                "Initial commit",
                {"app.py": "value = 1\n"},
            )

            with self.assertRaisesRegex(ValueError, "Root commits"):
                extract_prefix_features(root, root_commit)

    def test_merge_commit_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)

            commit_files(
                root,
                "Initial commit",
                {"app.py": "value = 1\n"},
            )

            run_git(root, "branch", "feature")
            run_git(root, "checkout", "feature")
            commit_files(
                root,
                "Feature change",
                {"feature.py": "value = 2\n"},
            )

            run_git(root, "checkout", "master")
            commit_files(
                root,
                "Main change",
                {"main.py": "value = 3\n"},
            )

            run_git(
                root,
                "merge",
                "--no-ff",
                "feature",
                "-m",
                "Merge feature",
            )

            merge_commit = run_git(root, "rev-parse", "HEAD")

            with self.assertRaisesRegex(ValueError, "Merge commits"):
                extract_prefix_features(root, merge_commit)


    def test_added_file_has_no_pre_fix_metrics(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)
            commit_files(root, "Initial source", {
                "src/app.py": "def app():\n    return 1\n"
            })
            fixing_commit = commit_files(root, "Add new module", {
                "src/new.py": "def new_function():\n    return 2\n"
            })
            result = extract_prefix_features(root, fixing_commit)
            self.assertEqual(result["new_file_count"], 1)
            self.assertIn("src/new.py", result["new_files_without_pre_fix_metrics"])
            self.assertNotIn("src/new.py", [
                item["file"] for item in result["file_features"]
            ])

    def test_deleted_file_uses_parent_snapshot_metrics(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)
            initial_source = (
                "def first():\n"
                "    return 1\n"
                "\n"
                "def second():\n"
                "    return 2\n"
            )
            commit_files(root, "Initial source", {
                "src/removed.py": initial_source
            })
            (root / "src/removed.py").unlink()
            run_git(root, "add", "-A")
            run_git(root, "commit", "-m", "Remove module")
            fixing_commit = run_git(root, "rev-parse", "HEAD")
            result = extract_prefix_features(root, fixing_commit)
            self.assertEqual(result["changed_python_file_count"], 1)
            self.assertEqual(result["feature_file_count"], 1)
            feature = result["file_features"][0]
            self.assertEqual(feature["file"], "src/removed.py")
            self.assertEqual(feature["change_status"], "D")
            self.assertEqual(feature["code_metrics"]["function_count"], 2)


    def test_prior_change_count_excludes_fixing_and_future_commits(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)

            commit_files(root, "Initial source", {
                "src/app.py": "value = 1\n"
            })
            commit_files(root, "Earlier modification", {
                "src/app.py": "value = 2\n"
            })
            fixing_commit = commit_files(root, "Fix application", {
                "src/app.py": "value = 3\n"
            })
            commit_files(root, "Future modification", {
                "src/app.py": "value = 4\n"
            })

            result = extract_prefix_features(root, fixing_commit)
            feature = result["file_features"][0]

            self.assertEqual(feature["prior_change_count"], 1)

    def test_invalid_commit_hash_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository(root)

            with self.assertRaises(RuntimeError):
                extract_prefix_features(root, "invalid-commit-hash")


if __name__ == "__main__":
    unittest.main()
