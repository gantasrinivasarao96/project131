"""Rule-based, explainable refactoring recommendations."""


def generate_refactoring_recommendations(
    graph: dict,
    code_metrics: list[dict],
) -> dict:
    """Recommend refactoring reviews based on graph and code metrics."""
    nodes = graph["nodes"]
    edges = graph["edges"]

    in_degree = {node: 0 for node in nodes}
    out_degree = {node: 0 for node in nodes}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        if source not in out_degree or target not in in_degree:
            raise ValueError("Graph edge references an unknown node")

        out_degree[source] += 1
        in_degree[target] += 1

    metrics_by_file = {
        item["file"]: item
        for item in code_metrics
    }

    recommendations = []

    for node in sorted(nodes):
        incoming = in_degree[node]
        outgoing = out_degree[node]
        metrics = metrics_by_file.get(node, {})
        lines = metrics.get("lines_of_code", 0)

        if incoming >= 3:
            recommendations.append({
                "file": node,
                "type": "high_fan_in",
                "priority": "medium",
                "evidence": {
                    "incoming_dependencies": incoming,
                },
                "reason": (
                    "Multiple modules depend on this module, "
                    "so changes may affect several dependents."
                ),
                "recommendation": (
                    "Review the public interface, add focused tests, "
                    "and assess change impact before refactoring."
                ),
            })

        if outgoing >= 3:
            recommendations.append({
                "file": node,
                "type": "high_fan_out",
                "priority": "medium",
                "evidence": {
                    "outgoing_dependencies": outgoing,
                },
                "reason": (
                    "This module depends on several other modules, "
                    "which may increase coupling and maintenance effort."
                ),
                "recommendation": (
                    "Review its responsibilities and consider separating "
                    "unrelated concerns behind clear interfaces."
                ),
            })

        if lines >= 300:
            recommendations.append({
                "file": node,
                "type": "large_source_file",
                "priority": "medium",
                "evidence": {
                    "lines_of_code": lines,
                },
                "reason": (
                    "The source file is large and may contain "
                    "multiple responsibilities."
                ),
                "recommendation": (
                    "Review the file and, where responsibilities are "
                    "distinct, split them into cohesive modules."
                ),
            })

    return {
        "method": "rule_based_refactoring_recommendations",
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "interpretation": (
            "Recommendations are heuristic review suggestions, "
            "not proof of defects or guaranteed improvements. "
            "Review each suggestion before making code changes."
        ),
    }
