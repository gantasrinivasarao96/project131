from pathlib import Path

from src.analysis.code_metrics import calculate_code_metrics
from src.analysis.change_impact import analyze_change_impact
from src.analysis.dependency_cycles import detect_dependency_cycles
from src.analysis.graph_metrics import calculate_graph_metrics
from src.analysis.git_history import analyze_git_history
from src.analysis.risk_analysis import calculate_structural_risk
from src.analysis.static_analysis import run_static_analysis
from src.graph.graph_builder import build_dependency_graph
from src.refactoring.recommendation_engine import generate_refactoring_recommendations


def analyze_repository(
    root: Path,
    changed_module: str | None = None,
) -> dict:
    """Analyze repository structure, code metrics, and static findings."""
    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

    python_files = sorted(root.rglob("*.py"))

    try:
        git_history = {
            "status": "completed",
            **analyze_git_history(root),
        }
    except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
        git_history = {
            "status": "unavailable",
            "reason": str(exc),
        }

    graph = build_dependency_graph(root)
    change_impact = (
        analyze_change_impact(graph, changed_module)
        if changed_module is not None
        else None
    )
    dependency_cycles = detect_dependency_cycles(graph)
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

    structural_risk = calculate_structural_risk(
        graph,
        code_metrics,
    )

    refactoring_recommendations = generate_refactoring_recommendations(
        graph,
        code_metrics,
    )

    return {
        "repository": root.name,
        "python_file_count": len(python_files),
        "dependency_graph": graph,
        "git_history": git_history,
        "change_impact": change_impact,
        "dependency_cycles": dependency_cycles,
        "graph_metrics": graph_metrics,
        "code_metrics": code_metrics,
        "parse_errors": parse_errors,
        "static_analysis": static_analysis,
        "structural_risk": structural_risk,
        "refactoring_recommendations": refactoring_recommendations,
    }
