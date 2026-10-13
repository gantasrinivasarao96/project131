from pathlib import Path

from src.analysis.code_metrics import calculate_code_metrics
from src.analysis.graph_metrics import calculate_graph_metrics
from src.analysis.static_analysis import run_static_analysis
from src.graph.graph_builder import build_dependency_graph


def analyze_repository(root: Path) -> dict:
    """Analyze repository dependencies, code metrics, and static findings."""
    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

    python_files = sorted(root.rglob("*.py"))

    graph = build_dependency_graph(root)
    graph_metrics = calculate_graph_metrics(graph)

    code_metrics = []
    parse_errors = []

    for file_path in python_files:
        relative_path = file_path.relative_to(root).as_posix()

        try:
            metrics = calculate_code_metrics(file_path)
            code_metrics.append({
                **metrics,
                "file": relative_path,
            })
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({
                "file": relative_path,
                "error": type(exc).__name__,
            })

    static_analysis = run_static_analysis(root)

    return {
        "repository": root.name,
        "python_file_count": len(python_files),
        "dependency_graph": graph,
        "graph_metrics": graph_metrics,
        "code_metrics": code_metrics,
        "parse_errors": parse_errors,
        "static_analysis": static_analysis,
    }
