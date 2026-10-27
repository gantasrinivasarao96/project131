"""Extract Git history and identify files that change together."""

from collections import Counter
from itertools import combinations
from pathlib import Path
import subprocess


def analyze_git_history(
    root: Path,
    max_commits: int = 500,
    min_cochange_count: int = 2,
) -> dict:
    """Analyze recent commit history and pairwise file co-changes."""
    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(f"Repository directory not found: {root}")

    if max_commits < 1:
        raise ValueError("max_commits must be at least 1")

    if min_cochange_count < 1:
        raise ValueError("min_cochange_count must be at least 1")

    repository_check = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if (
        repository_check.returncode != 0
        or repository_check.stdout.strip() != "true"
    ):
        raise ValueError(f"Not a Git working tree: {root}")

    top_level = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if top_level.returncode != 0:
        raise ValueError(f"Could not determine Git root: {root}")

    if Path(top_level.stdout.strip()).resolve() != root:
        raise ValueError(
            "Analysis directory must be the Git repository root "
            "for Git-history analysis"
        )

    result = subprocess.run(
        [
            "git", "-C", str(root),
            "log",
            f"-n{max_commits}",
            "--format=COMMIT:%H",
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
        raise RuntimeError(
            "Git history extraction failed: "
            + result.stderr.strip()
        )

    commit_files = []
    current_files = None

    for line in result.stdout.splitlines():
        if line.startswith("COMMIT:"):
            if current_files is not None:
                commit_files.append(sorted(current_files))

            current_files = set()
            continue

        if current_files is not None and line.strip():
            current_files.add(line.strip())

    if current_files is not None:
        commit_files.append(sorted(current_files))

    pair_counts = Counter()

    for files in commit_files:
        # Each file pair contributes at most once per commit.
        pair_counts.update(combinations(files, 2))

    cochange_pairs = [
        {
            "file_a": file_a,
            "file_b": file_b,
            "cochange_count": count,
        }
        for (file_a, file_b), count in sorted(pair_counts.items())
        if count >= min_cochange_count
    ]

    return {
        "method": "git_commit_pairwise_cochange",
        "repository": root.name,
        "commit_count": len(commit_files),
        "max_commits": max_commits,
        "min_cochange_count": min_cochange_count,
        "cochange_pair_count": len(cochange_pairs),
        "cochange_pairs": cochange_pairs,
        "interpretation": (
            "Co-change indicates files that were modified together "
            "in the analyzed history. It does not establish a defect, "
            "causal relationship, or architectural dependency."
        ),
    }
