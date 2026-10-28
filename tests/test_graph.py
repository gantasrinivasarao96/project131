from pathlib import Path
from tempfile import TemporaryDirectory

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


def test_src_layout_dependency_resolution():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        (root / "src/sample").mkdir(parents=True)
        (root / "tests").mkdir()

        (root / "src/sample/__init__.py").write_text(
            "", encoding="utf-8"
        )
        (root / "src/sample/simple.py").write_text(
            "def add_one(number):\n"
            "    return number + 1\n",
            encoding="utf-8",
        )
        (root / "tests/test_simple.py").write_text(
            "from sample.simple import add_one\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "tests/test_simple.py",
            "src/sample/simple.py",
        )
        assert expected in edges, edges

    print("PASS: src/ package import resolves to the correct file.")


if __name__ == "__main__":
    test_sample_dependency_graph()
    test_src_layout_dependency_resolution()


def test_relative_import_dependency_resolution():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "src" / "sample"
        package.mkdir(parents=True)

        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "simple.py").write_text(
            "def add_one(number):\n"
            "    return number + 1\n",
            encoding="utf-8",
        )
        (package / "helper.py").write_text(
            "from .simple import add_one\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "src/sample/helper.py",
            "src/sample/simple.py",
        )
        assert expected in edges, edges

    print("PASS: Relative package import resolves to the correct file.")


if __name__ == "__main__":
    test_sample_dependency_graph()
    test_src_layout_dependency_resolution()
    test_relative_import_dependency_resolution()
