from pathlib import Path

from src.analysis.graph_metrics import calculate_graph_metrics
from src.graph.graph_builder import build_dependency_graph


def test_sample_graph_metrics():
    graph = build_dependency_graph(
        Path("data/sample/demo_project")
    )

    metrics = calculate_graph_metrics(graph)

    assert metrics["node_count"] == 3
    assert metrics["edge_count"] == 2

    assert metrics["out_degree"]["main.py"] == 1
    assert metrics["in_degree"]["auth.py"] == 1
    assert metrics["out_degree"]["auth.py"] == 1
    assert metrics["in_degree"]["database.py"] == 1

    assert metrics["isolated_nodes"] == []

    print("PASS: Graph metrics verified.")


if __name__ == "__main__":
    test_sample_graph_metrics()
