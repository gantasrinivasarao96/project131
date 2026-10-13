from collections import Counter


def calculate_graph_metrics(graph: dict) -> dict:
    """Calculate basic structural metrics for a dependency graph."""
    nodes = graph["nodes"]
    edges = graph["edges"]

    in_degree = Counter({node: 0 for node in nodes})
    out_degree = Counter({node: 0 for node in nodes})

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        if source not in out_degree or target not in in_degree:
            raise ValueError("Graph edge references an unknown node")

        out_degree[source] += 1
        in_degree[target] += 1

    isolated_nodes = sorted(
        node
        for node in nodes
        if in_degree[node] == 0 and out_degree[node] == 0
    )

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "in_degree": dict(sorted(in_degree.items())),
        "out_degree": dict(sorted(out_degree.items())),
        "isolated_nodes": isolated_nodes,
    }
