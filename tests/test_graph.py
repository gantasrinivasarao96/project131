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


def test_from_package_import_resolution():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "src/sample"
        package.mkdir(parents=True)

        (package / "__init__.py").write_text(
            "from . import simple\n",
            encoding="utf-8",
        )
        (package / "simple.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        assert (
            "src/sample/__init__.py",
            "src/sample/simple.py",
        ) in edges, edges

    print("PASS: from . import simple resolves correctly.")


def test_parent_package_import_resolution():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        common = root / "src/sample/common"
        nested = root / "src/sample/sub"
        common.mkdir(parents=True)
        nested.mkdir(parents=True)

        for init_file in (
            root / "src/sample/__init__.py",
            common / "__init__.py",
            nested / "__init__.py",
        ):
            init_file.write_text("", encoding="utf-8")

        (common / "helper.py").write_text(
            "VALUE = 1\n".replace("\\n", "\n"),
            encoding="utf-8",
        )
        (nested / "consumer.py").write_text(
            "from ..common import helper\n".replace("\\n", "\n"),
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "src/sample/sub/consumer.py",
            "src/sample/common/helper.py",
        )
        assert expected in edges, edges

    print("PASS: parent-package submodule import resolves correctly.")

def test_package_import_selects_submodule():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "src" / "sample"
        package.mkdir(parents=True)

        (package / "__init__.py").write_text(
            "from . import hooks\n",
            encoding="utf-8",
        )
        (package / "hooks.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        (package / "utils.py").write_text(
            "VALUE = 2\n",
            encoding="utf-8",
        )
        (root / "tests").mkdir()
        (root / "tests" / "test_hooks.py").write_text(
            "from sample import hooks\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "tests/test_hooks.py",
            "src/sample/hooks.py",
        )
        assert expected in edges, edges

        print("PASS: package import resolves to its submodule.")


def test_direct_package_import_resolves_initializer():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "src" / "sample"
        package.mkdir(parents=True)
        (root / "tests").mkdir()

        (package / "__init__.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        (root / "tests" / "test_package.py").write_text(
            "import sample\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "tests/test_package.py",
            "src/sample/__init__.py",
        )
        assert expected in edges, edges

    print("PASS: direct package import resolves to __init__.py.")


def test_relative_package_attribute_import():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        tests_dir = root / "tests"
        tests_dir.mkdir()

        (tests_dir / "__init__.py").write_text(
            "SNIMissingWarning = None\n",
            encoding="utf-8",
        )
        (tests_dir / "test_requests.py").write_text(
            "from . import SNIMissingWarning\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "tests/test_requests.py",
            "tests/__init__.py",
        )
        assert expected in edges, edges

    print("PASS: relative package attribute resolves to __init__.py.")


def test_nested_relative_package_attribute_import():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "src" / "sample"
        nested = package / "sub"
        nested.mkdir(parents=True)

        (package / "__init__.py").write_text(
            "PARENT_ATTRIBUTE = 1\n",
            encoding="utf-8",
        )
        (nested / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        (nested / "consumer.py").write_text(
            "from .. import PARENT_ATTRIBUTE\n",
            encoding="utf-8",
        )

        graph = build_dependency_graph(root)
        edges = {
            (edge["source"], edge["target"])
            for edge in graph["edges"]
        }

        expected = (
            "src/sample/sub/consumer.py",
            "src/sample/__init__.py",
        )
        assert expected in edges, edges

    print("PASS: nested relative package attribute resolves correctly.")

if __name__ == "__main__":
    test_sample_dependency_graph()
    test_src_layout_dependency_resolution()
    test_relative_import_dependency_resolution()
    test_from_package_import_resolution()
    test_parent_package_import_resolution()
    test_package_import_selects_submodule()
    test_direct_package_import_resolves_initializer()
    test_relative_package_attribute_import()
    test_nested_relative_package_attribute_import()
