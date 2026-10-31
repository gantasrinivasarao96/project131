"""Command-line interface for Project 131 repository analysis."""

import argparse
import sys
import tempfile
from pathlib import Path

from src.analysis.repository_analyzer import analyze_repository
from src.ingestion.zip_ingestion import extract_source_zip
from src.reporting.json_report import save_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a Python repository or ZIP archive for dependencies, "
            "structural risks, static findings, and refactoring opportunities."
        )
    )

    parser.add_argument(
        "repository",
        type=Path,
        help="Path to a repository directory or source-code ZIP archive.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/project131_report.json"),
        help=(
            "JSON report destination "
            "(default: reports/project131_report.json)."
        ),
    )

    parser.add_argument(
        "--changed-module",
        help=(
            "Optional repository-relative module path, such as "
            "src/main.py, for change-impact analysis."
        ),
    )

    parser.add_argument(
        "--fixing-commit",
        help=(
            "Optional Git commit that fixes a defect. Extracts features "
            "from its parent snapshot for prefix-based analysis. "
            "Requires a Git repository directory, not a ZIP archive."
        ),
    )

    return parser


def _find_python_project(extraction_root: Path) -> Path:
    """Find the project root in an extracted archive."""
    python_files = list(extraction_root.rglob("*.py"))

    if not python_files:
        raise ValueError(
            "ZIP archive contains no Python source files."
        )

    if any(path.parent == extraction_root for path in python_files):
        return extraction_root

    first_parts = {
        path.relative_to(extraction_root).parts[0]
        for path in python_files
    }

    if len(first_parts) == 1:
        candidate = extraction_root / next(iter(first_parts))

        if candidate.is_dir() and any(candidate.rglob("*.py")):
            return candidate

    return extraction_root


def _analyze_and_report(
    repository: Path,
    output: Path,
    changed_module: str | None,
    fixing_commit: str | None,
) -> tuple[dict, Path]:
    report = analyze_repository(
        repository,
        changed_module=changed_module,
        fixing_commit=fixing_commit,
    )

    output_path = save_json_report(report, output)
    return report, output_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source = args.repository.expanduser().resolve()

    if not source.exists():
        parser.error(f"input path does not exist: {source}")

    if args.fixing_commit is not None and not source.is_dir():
        parser.error(
            "--fixing-commit requires a Git repository directory; "
            "it cannot be used with a ZIP archive."
        )

    try:
        if source.is_dir():
            repository = source

            report, output_path = _analyze_and_report(
                repository,
                args.output,
                args.changed_module,
                args.fixing_commit,
            )

        elif source.is_file() and source.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory(
                prefix="project131_"
            ) as workspace:
                extracted_root = extract_source_zip(
                    source,
                    Path(workspace) / "extracted",
                )

                repository = _find_python_project(extracted_root)

                report, output_path = _analyze_and_report(
                    repository,
                    args.output,
                    args.changed_module,
                    fixing_commit=None,
                )

        else:
            parser.error(
                "input must be a repository directory or a .zip archive"
            )

    except (
        OSError,
        ValueError,
        RuntimeError,
        TimeoutError,
    ) as exc:
        print(
            f"Project 131 analysis failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print("PROJECT 131 - REPOSITORY ANALYSIS")
    print("=" * 40)
    print(f"Input: {source}")
    print(f"Analyzed project: {repository.name}")
    print(f"Python files: {report['python_file_count']}")
    print(
        f"Dependency nodes: "
        f"{report['graph_metrics']['node_count']}"
    )
    print(
        f"Dependency edges: "
        f"{report['graph_metrics']['edge_count']}"
    )
    print(
        "Review-priority results: "
        f"{report['risk_baseline']['module_count']}"
    )

    if report["prefix_features"] is not None:
        print("Prefix features: extracted")

    print(f"JSON report saved to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
