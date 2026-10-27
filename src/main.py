"""Command-line interface for Project 131 repository analysis."""

import argparse
import sys
from pathlib import Path

from src.analysis.repository_analyzer import analyze_repository
from src.reporting.json_report import save_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a Python repository for dependencies, "
            "structural risks, static findings, and refactoring "
            "opportunities."
        )
    )
    parser.add_argument(
        "repository",
        type=Path,
        help="Path to the repository or source directory to analyze.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/project131_report.json"),
        help="JSON report destination (default: reports/project131_report.json).",
    )
    parser.add_argument(
        "--changed-module",
        help=(
            "Optional repository-relative module path, such as "
            "src/main.py, for change-impact analysis."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repository = args.repository.expanduser().resolve()

    if not repository.is_dir():
        parser.error(f"repository directory does not exist: {repository}")

    try:
        report = analyze_repository(
            repository,
            changed_module=args.changed_module,
        )
        output_path = save_json_report(report, args.output)

    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print(f"Project 131 analysis failed: {exc}", file=sys.stderr)
        return 1

    print("PROJECT 131 - REPOSITORY ANALYSIS")
    print("=" * 40)
    print(f"Repository: {repository}")
    print(f"Python files: {report['python_file_count']}")
    print(f"Dependency nodes: {report['graph_metrics']['node_count']}")
    print(f"Dependency edges: {report['graph_metrics']['edge_count']}")
    print(
        "Review-priority results: "
        f"{report['risk_baseline']['module_count']}"
    )
    print(f"JSON report saved to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
