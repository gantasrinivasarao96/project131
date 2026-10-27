"""Transparent heuristic baseline for prioritizing defect-risk review."""


def calculate_risk_baseline(
    graph: dict,
    code_metrics: list[dict],
    git_history: dict | None = None,
) -> dict:
    """Score modules using explicit structural and co-change evidence."""
    nodes = graph["nodes"]
    known_nodes = set(nodes)

    if len(known_nodes) != len(nodes):
        raise ValueError("Graph contains duplicate nodes")

    in_degree = {node: 0 for node in nodes}
    out_degree = {node: 0 for node in nodes}

    for edge in graph["edges"]:
        source = edge["source"]
        target = edge["target"]

        if source not in known_nodes or target not in known_nodes:
            raise ValueError("Graph edge references an unknown node")

        out_degree[source] += 1
        in_degree[target] += 1

    metrics_by_file = {
        item["file"]: item
        for item in code_metrics
    }

    cochange_counts = {node: 0 for node in nodes}

    if git_history and git_history.get("status", "completed") == "completed":
        for pair in git_history.get("cochange_pairs", []):
            file_a = pair["file_a"]
            file_b = pair["file_b"]
            count = pair["cochange_count"]

            if count < 2:
                continue

            if file_a in cochange_counts:
                cochange_counts[file_a] += 1

            if file_b in cochange_counts:
                cochange_counts[file_b] += 1

    results = []

    for node in sorted(nodes):
        metrics = metrics_by_file.get(node, {})
        lines = metrics.get("lines_of_code", 0)
        evidence = []
        score = 0

        if in_degree[node] >= 3:
            score += 1
            evidence.append({
                "type": "high_in_degree",
                "description": (
                    f"{in_degree[node]} modules depend on this module."
                ),
            })

        if out_degree[node] >= 3:
            score += 1
            evidence.append({
                "type": "high_out_degree",
                "description": (
                    f"This module depends on {out_degree[node]} modules."
                ),
            })

        if lines >= 300:
            score += 1
            evidence.append({
                "type": "large_source_file",
                "description": f"Source file contains {lines} lines.",
            })

        if cochange_counts[node] > 0:
            score += 1
            evidence.append({
                "type": "repeated_cochange",
                "description": (
                    "This module repeatedly changed alongside "
                    "at least one other file."
                ),
            })

        if score >= 3:
            priority = "high"
        elif score >= 1:
            priority = "medium"
        else:
            priority = "low"

        results.append({
            "file": node,
            "review_score": score,
            "maximum_score": 4,
            "review_priority": priority,
            "evidence": evidence,
        })

    results.sort(
        key=lambda item: (
            -item["review_score"],
            item["file"],
        )
    )

    return {
        "method": "transparent_rule_based_review_baseline",
        "label": "review_priority_not_defect_probability",
        "module_count": len(results),
        "results": results,
        "interpretation": (
            "Scores prioritize manual review using structural and "
            "historical co-change indicators. This is not a trained "
            "defect predictor, a calibrated probability, or evidence "
            "that a defect exists. Git history may be unavailable "
            "or incomplete."
        ),
    }
