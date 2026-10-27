"""Analyze which modules may be affected by a module change."""


def analyze_change_impact(graph: dict, changed_module: str) -> dict:
    """Find direct and transitive dependents of a changed module."""
    nodes = graph["nodes"]
    edges = graph["edges"]
    known_nodes = set(nodes)

    if len(known_nodes) != len(nodes):
        raise ValueError("Graph contains duplicate nodes")

    if changed_module not in known_nodes:
        raise ValueError(
            f"Changed module is not present in graph: {changed_module}"
        )

    # Edges point from importer to imported module.
    # Reverse edges to find modules that depend on the changed module.
    dependents = {node: set() for node in nodes}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        if source not in known_nodes or target not in known_nodes:
            raise ValueError("Graph edge references an unknown node")

        dependents[target].add(source)

    direct = sorted(dependents[changed_module])
    visited = {changed_module}
    pending = list(direct)
    impacted = set()

    while pending:
        module = pending.pop()

        if module in visited:
            continue

        visited.add(module)
        impacted.add(module)
        pending.extend(dependents[module] - visited)

    return {
        "method": "reverse_dependency_traversal",
        "changed_module": changed_module,
        "direct_dependents": direct,
        "transitive_dependents": sorted(impacted - set(direct)),
        "impacted_modules": sorted(impacted),
        "impact_count": len(impacted),
        "interpretation": (
            "Impact is estimated from the available static dependency "
            "graph. It identifies potential dependents, not confirmed "
            "runtime failures or guaranteed breakages."
        ),
    }
