
import tempfile
import unittest
from pathlib import Path

from src.graph.graph_builder import build_dependency_graph


class TestBuildDependencyGraph(unittest.TestCase):
    def test_excludes_virtual_environment_and_build_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            (root / "src").mkdir()
            (root / ".venv" / "lib").mkdir(parents=True)
            (root / "build").mkdir()

            (root / "src" / "main.py").write_text(
                "from src import utils\n",
                encoding="utf-8",
            )
            (root / "src" / "utils.py").write_text(
                "def helper():\n    return 1\n",
                encoding="utf-8",
            )
            (root / ".venv" / "lib" / "external.py").write_text(
                "def external():\n    pass\n",
                encoding="utf-8",
            )
            (root / "build" / "generated.py").write_text(
                "def generated():\n    pass\n",
                encoding="utf-8",
            )

            graph = build_dependency_graph(root)

            self.assertEqual(
                set(graph["nodes"]),
                {"src/main.py", "src/utils.py"},
            )
            self.assertEqual(
                graph["edges"],
                [{"source": "src/main.py", "target": "src/utils.py"}],
            )


if __name__ == "__main__":
    unittest.main()
