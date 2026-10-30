"""Extract historical commits and identify candidate defect-fixing changes."""

import re
import subprocess
from pathlib import Path

FIX_PATTERN = re.compile(
    r"\b(fix|bugfix|bug|regression|correct|prevent)\b",
    re.IGNORECASE,
)


def extract_historical_commits(
    root: Path,
    max_commits: int = 500,
) -> dict:
    """Extract commit metadata and classify potential defect-fix candidates."""

    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

    if max_commits < 1:
        raise ValueError("max_commits must be at least 1")

    check = subprocess.run(
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

    if check.returncode != 0 or check.stdout.strip() != "true":
        raise ValueError(f"Not a Git repository: {root}")

    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "log",
            f"-n{max_commits}",
            "--format=%H%x09%ct%x09%s",
            "--name-only",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )

    if result.returncode != 0:
        if "does not have any commits yet" in result.stderr:
            return {
                "method": "historical_git_commit_candidate_extraction",
                "repository": root.name,
                "commit_count": 0,
                "candidate_defect_fix_count": 0,
                "unlabeled_commit_count": 0,
                "commits": [],
                "interpretation": (
                    "Repository has no commits to analyze."
                ),
            }

        raise RuntimeError(
            "Historical commit extraction failed: "
            + result.stderr.strip()
        )

    commits = []
    current = None

    def save_current():
        if current is None:
            return

        changed_files = sorted(current["changed_files"])

        production_files = [
            name
            for name in changed_files
            if name.endswith(".py")
            and not (
                name.startswith("tests/")
                or "/tests/" in name
                or Path(name).name.startswith("test_")
            )
        ]

        test_files = [
            name
            for name in changed_files
            if name.endswith(".py")
            and (
                name.startswith("tests/")
                or "/tests/" in name
                or Path(name).name.startswith("test_")
            )
        ]

        candidate = bool(
            FIX_PATTERN.search(current["message"])
        )

        commits.append(
            {
                "commit_hash": current["commit_hash"],
                "timestamp": current["timestamp"],
                "message": current["message"],
                "changed_files": changed_files,
                "production_files": production_files,
                "test_files": test_files,
                "candidate_defect_fix": candidate,
                "label": (
                    "needs_review"
                    if candidate
                    else "unlabeled"
                ),
                "labeling_method": (
                    "commit_message_keyword_candidate"
                ),
            }
        )

    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)

        if len(parts) == 3 and parts[1].isdigit():
            save_current()

            current = {
                "commit_hash": parts[0],
                "timestamp": int(parts[1]),
                "message": parts[2],
                "changed_files": set(),
            }

        elif current is not None and line:
            current["changed_files"].add(line)

    save_current()

    candidates = sum(
        item["candidate_defect_fix"]
        for item in commits
    )

    return {
        "method": "historical_git_commit_candidate_extraction",
        "repository": root.name,
        "commit_count": len(commits),
        "candidate_defect_fix_count": candidates,
        "unlabeled_commit_count": len(commits) - candidates,
        "commits": commits,
        "interpretation": (
            "Commit-message keywords identify candidates only. "
            "They do not confirm defects or provide ground-truth labels."
        ),
    }
