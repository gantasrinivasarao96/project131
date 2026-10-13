from pathlib import Path

from src.graph.graph_builder import build_dependency_graph


def test_sample_dependency_graph():
    root = Path("data/sample/demo_project")
    graph = build_dependency_graph(root)

    assert len(graph["nodes"]) == 3, graph
    assert len(graph["edges"]) == 2, graph

    edges = {
        (edge["source"], edge["target"])
        for edge in graph["edges"]
    }

    assert ("main.py", "auth.py") in edges, edges
    assert ("auth.py", "database.py") in edges, edges

    print("PASS: Three nodes and two dependency edges verified.")


if __name__ == "__main__":
    test_sample_dependency_graph()
