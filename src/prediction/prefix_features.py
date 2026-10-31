"""Extract pre-fix features from a fixing commit's parent snapshot."""

import io
import subprocess
import tarfile
import tempfile
from pathlib import Path

from src.analysis.code_metrics import calculate_source_metrics
from src.analysis.graph_metrics import calculate_graph_metrics
from src.graph.graph_builder import build_dependency_graph


def _git(root: Path, *args: str) -> str:
    """Run a Git command and return its standard output."""
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {result.stderr.strip()}"
        )

    return result.stdout



def _count_prior_file_changes(
    root: Path,
    parent_commit: str,
    target_files: set[str],
) -> dict[str, int]:
    """Count prior commits modifying target files, excluding initial additions."""
    counts = {file_path: 0 for file_path in target_files}
    if not target_files:
        return counts

    result = subprocess.run(
        [
            "git", "-C", str(root), "log", parent_commit,
            "--format=COMMIT:%H", "--name-status", "-z", "--no-renames",
        ],
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git history extraction failed: {error}")

    entries = result.stdout.split(b"\0")
    current_commit_files = set()
    index = 0

    def record_commit():
        for file_path in current_commit_files:
            counts[file_path] += 1
        current_commit_files.clear()

    while index < len(entries):
        status_entry = entries[index].lstrip(b"\n")
        index += 1
        if not status_entry:
            continue
        if status_entry.startswith(b"COMMIT:"):
            record_commit()
            continue

        status = status_entry.decode("ascii", errors="replace")
        if index >= len(entries):
            break
        file_path = entries[index].decode("utf-8", errors="replace")
        index += 1

        if status != "A" and file_path in target_files:
            current_commit_files.add(file_path)

    record_commit()
    return counts

def extract_prefix_features(
    root: Path,
    fixing_commit: str,
) -> dict:
    """Extract features using only the fixing commit's parent snapshot."""
    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

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

    commit = _git(
        root,
        "rev-parse",
        "--verify",
        f"{fixing_commit}^{{commit}}",
    ).strip()

    history = _git(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        commit,
    ).split()

    if len(history) < 2:
        raise ValueError(
            "Root commits cannot be used for pre-fix feature extraction"
        )

    if len(history) > 2:
        raise ValueError(
            "Merge commits cannot be used for pre-fix feature extraction"
        )

    parent = history[1]

    changed_result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            "--no-renames",
            "-z",
            parent,
            commit,
        ],
        capture_output=True,
        check=False,
        timeout=120,
    )

    if changed_result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {changed_result.stderr.decode(errors='replace').strip()}"
        )

    changed_fields = changed_result.stdout.split(bytes([0]))
    changed_files = []

    for index in range(0, len(changed_fields) - 1, 2):
        status = changed_fields[index].decode("ascii")
        relative_path = changed_fields[index + 1].decode(
            "utf-8",
            errors="surrogateescape",
        )

        if relative_path.endswith(".py"):
            changed_files.append(
                {
                    "file": relative_path,
                    "change_status": status,
                }
            )

    changed_files.sort(key=lambda item: item["file"])

    with tempfile.TemporaryDirectory(
        prefix="project131_prefix_"
    ) as temporary_directory:
        snapshot = Path(temporary_directory)

        archive = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "archive",
                "--format=tar",
                parent,
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )

        if archive.returncode != 0:
            error = archive.stderr.decode(
                "utf-8",
                errors="replace",
            ).strip()

            raise RuntimeError(
                f"Could not create parent snapshot: {error}"
            )

        with tarfile.open(
            fileobj=io.BytesIO(archive.stdout),
            mode="r:",
        ) as tar:
            tar.extractall(snapshot, filter="data")

        graph = build_dependency_graph(snapshot)
        graph_metrics = calculate_graph_metrics(graph)

        historical_counts = _count_prior_file_changes(
            root,
            parent,
            {
                item["file"]
                for item in changed_files
                if item["change_status"] != "A"
            },
        )

        file_features = []
        new_files_without_prefix = []
        parse_errors = []
        unavailable_files = []

        for item in changed_files:
            relative_path = item["file"]
            status = item["change_status"]
            source_path = snapshot / relative_path

            if status == "A":
                new_files_without_prefix.append(relative_path)
                continue

            if not source_path.is_file():
                unavailable_files.append(relative_path)
                continue

            try:
                source = source_path.read_text(encoding="utf-8")

                code_metrics = calculate_source_metrics(
                    source,
                    filename=relative_path,
                )

            except (OSError, SyntaxError, UnicodeDecodeError):
                parse_errors.append(relative_path)
                continue

            file_features.append(
                {
                    "file": relative_path,
                    "change_status": status,
                    "prior_change_count": historical_counts.get(
                        relative_path, 0
                    ),
                    "code_metrics": code_metrics,
                    "in_degree": graph_metrics["in_degree"].get(
                        relative_path, 0
                    ),
                    "out_degree": graph_metrics["out_degree"].get(
                        relative_path, 0
                    ),
                    "is_isolated": (
                        relative_path in graph_metrics["isolated_nodes"]
                    ),
                }
            )

        return {
            "method": "pre_fix_parent_snapshot",
            "repository": root.name,
            "fixing_commit": commit,
            "parent_commit": parent,
            "changed_python_file_count": len(changed_files),
            "feature_file_count": len(file_features),
            "new_file_count": len(new_files_without_prefix),
            "new_files_without_pre_fix_metrics": (
                new_files_without_prefix
            ),
            "parse_error_count": len(parse_errors),
            "parse_errors": parse_errors,
            "unavailable_files": unavailable_files,
            "graph_metrics": {
                "node_count": graph_metrics["node_count"],
                "edge_count": graph_metrics["edge_count"],
            },
            "file_features": file_features,
            "interpretation": (
                "Features are calculated from the fixing commit's parent "
                "snapshot. Modified and deleted files use their parent "
                "versions. Newly added files have no pre-fix file-level "
                "metrics. These features do not prove that a file contains "
                "a defect."
            ),
        }
