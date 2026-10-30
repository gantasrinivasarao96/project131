"""Detect circular dependencies in a directed module graph."""


def detect_dependency_cycles(graph: dict) -> dict:
    """Return strongly connected groups that contain dependency cycles."""
    nodes = graph["nodes"]
    edges = graph["edges"]

    known_nodes = set(nodes)

    if len(known_nodes) != len(nodes):
        raise ValueError("Graph contains duplicate nodes")

    adjacency = {node: [] for node in nodes}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        if source not in known_nodes or target not in known_nodes:
            raise ValueError("Graph edge references an unknown node")

        adjacency[source].append(target)

    for node, neighbors in adjacency.items():
        adjacency[node] = sorted(set(neighbors))

    index = 0
    indices = {}
    lowlinks = {}
    stack = []
    on_stack = set()
    components = []

    def strongconnect(node):
        nonlocal index

        indices[node] = index
        lowlinks[node] = index
        index += 1

        stack.append(node)
        on_stack.add(node)

        for neighbor in adjacency[node]:
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(
                    lowlinks[node],
                    lowlinks[neighbor],
                )
            elif neighbor in on_stack:
                lowlinks[node] = min(
                    lowlinks[node],
                    indices[neighbor],
                )

        if lowlinks[node] == indices[node]:
            component = []

            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)

                if member == node:
                    break

            components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            strongconnect(node)

    cycles = []

    for component in components:
        is_multi_node_cycle = len(component) > 1
        is_self_loop = (
            len(component) == 1
            and component[0] in adjacency[component[0]]
        )

        if is_multi_node_cycle or is_self_loop:
            cycles.append({
                "modules": component,
                "size": len(component),
                "type": (
                    "self_loop" if is_self_loop
                    else "circular_dependency_group"
                ),
            })

    cycles.sort(key=lambda item: item["modules"])

    return {
        "method": "tarjan_strongly_connected_components",
        "cycle_group_count": len(cycles),
        "cycles": cycles,
        "interpretation": (
            "Each reported group contains modules that can reach "
            "one another through directed dependencies. Review the "
            "group to determine whether the circular dependency "
            "should be refactored."
        ),
    }
