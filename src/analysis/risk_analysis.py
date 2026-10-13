def calculate_structural_risk(
    graph: dict,
    code_metrics: list[dict],
) -> dict:
    """Identify structural risk indicators using graph and code metrics."""
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

    findings = []

    for node in nodes:
        incoming = in_degree[node]
        outgoing = out_degree[node]
        metrics = metrics_by_file.get(node, {})

        indicators = []

        if incoming >= 3:
            indicators.append({
                "type": "high_in_degree",
                "description": (
                    "Several modules depend on this module; "
                    "changes may affect multiple dependents."
                ),
            })

        if outgoing >= 3:
            indicators.append({
                "type": "high_out_degree",
                "description": (
                    "This module depends on several other modules."
                ),
            })

        lines = metrics.get("lines_of_code", 0)

        if lines >= 300:
            indicators.append({
                "type": "large_source_file",
                "description": (
                    "The source file is large and may benefit "
                    "from maintainability review."
                ),
            })

        if indicators:
            findings.append({
                "file": node,
                "in_degree": incoming,
                "out_degree": outgoing,
                "lines_of_code": lines,
                "indicators": indicators,
            })

    return {
        "method": "rule_based_structural_indicators",
        "thresholds": {
            "high_in_degree": 3,
            "high_out_degree": 3,
            "large_source_file_lines": 300,
        },
        "finding_count": len(findings),
        "findings": findings,
        "interpretation": (
            "These indicators identify structural concerns. "
            "They are not confirmed defects or calibrated "
            "defect probabilities."
        ),
    }
