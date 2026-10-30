"""Inspect Git commits and collect evidence for manual defect validation."""

import subprocess
from pathlib import Path

REVIEW_STATUSES = {"confirmed", "rejected", "uncertain"}


def _run_git(
    root: Path,
    *args: str,
    timeout: int = 60,
) -> str:
    """Run a Git command and return its standard output."""

    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {result.stderr.strip()}"
        )

    return result.stdout


def _classify_file(path: str) -> str:
    """Classify a changed file using its repository path."""

    name = Path(path).name
    lower_path = path.lower()

    if (
        path.startswith("tests/")
        or "/tests/" in lower_path
        or name.startswith("test_")
        or name.endswith("_test.py")
    ):
        return "test"

    if path.startswith(".github/workflows/"):
        return "ci_cd"

    if name in {
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
    } or name.endswith((".lock", ".toml")):
        return "configuration_or_dependency"

    if name.endswith((".md", ".rst", ".txt")):
        return "documentation"

    if path.endswith(".py"):
        return "production"

    return "other"


def inspect_commit(
    root: Path,
    commit_hash: str,
    review_status: str = "uncertain",
) -> dict:
    """Inspect one commit and collect evidence for manual review.

    The review status is supplied by the reviewer. Git metadata and
    patch contents never automatically confirm a defect.
    """

    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            f"Invalid review status: {review_status}"
        )

    repository_check = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "rev-parse",
            "--is-inside-work-tree",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if (
        repository_check.returncode != 0
        or repository_check.stdout.strip() != "true"
    ):
        raise ValueError(f"Not a Git repository: {root}")

    verified_hash = _run_git(
        root,
        "rev-parse",
        "--verify",
        f"{commit_hash}^{{commit}}",
    ).strip()

    metadata = _run_git(
        root,
        "show",
        "-s",
        "--format=%H%x09%P%x09%ct%x09%s",
        verified_hash,
    ).strip()

    parts = metadata.split("\t", 3)

    if len(parts) != 4:
        raise RuntimeError("Unable to parse commit metadata")

    actual_hash, parents, timestamp, message = parts

    parent_hashes = parents.split() if parents else []

    if len(parent_hashes) > 1:
        raise ValueError(
            "Merge commits are not supported by this validator"
        )

    changed_output = _run_git(
        root,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-status",
        "-r",
        "--no-renames",
        verified_hash,
    )

    changed_files = []

    for line in changed_output.splitlines():
        fields = line.split("\t", 1)

        if len(fields) != 2:
            continue

        status, path = fields

        changed_files.append(
            {
                "path": path,
                "status": status,
                "category": _classify_file(path),
            }
        )

    numstat_output = _run_git(
        root,
        "show",
        "--format=",
        "--numstat",
        "--no-renames",
        verified_hash,
    )

    line_counts = {}

    for line in numstat_output.splitlines():
        fields = line.split("\t", 2)

        if len(fields) != 3:
            continue

        added, deleted, path = fields

        line_counts[path] = {
            "added": int(added) if added.isdigit() else None,
            "deleted": int(deleted) if deleted.isdigit() else None,
            "binary": added == "-" or deleted == "-",
        }

    for item in changed_files:
        item["line_changes"] = line_counts.get(
            item["path"],
            {
                "added": None,
                "deleted": None,
                "binary": False,
            },
        )

    patch = _run_git(
        root,
        "show",
        "--format=",
        "--no-ext-diff",
        "--no-renames",
        verified_hash,
    )

    category_counts = {}

    for item in changed_files:
        category = item["category"]
        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

    return {
        "repository": root.name,
        "commit_hash": actual_hash,
        "parent_hashes": parent_hashes,
        "timestamp": int(timestamp),
        "message": message,
        "changed_file_count": len(changed_files),
        "changed_files": changed_files,
        "category_counts": category_counts,
        "patch_available": bool(patch),
        "patch": patch,
        "review_status": review_status,
        "label_source": "manual_reviewer",
        "interpretation": (
            "Commit metadata and patch contents are evidence only. "
            "Defect status must be determined through manual review."
        ),
    }
