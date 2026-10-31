import unittest
from pathlib import Path

from src.analysis.code_metrics import (
    calculate_code_metrics,
    calculate_source_metrics,
)


class TestCodeMetrics(unittest.TestCase):

    def test_sample_code_metrics(self):
        metrics = calculate_code_metrics(
            Path("data/sample/demo_project/auth.py")
        )

        self.assertEqual(metrics["file"], "auth.py")
        self.assertEqual(metrics["function_count"], 1)
        self.assertEqual(metrics["class_count"], 0)
        self.assertEqual(metrics["import_count"], 1)
        self.assertGreater(metrics["lines_of_code"], 0)

    def test_source_metrics(self):
        source = (
            "import os\n"
            "\n"
            "class Example:\n"
            "    def run(self):\n"
            "        return os.getcwd()\n"
        )

        metrics = calculate_source_metrics(
            source,
            filename="example.py",
        )

        self.assertEqual(
            metrics,
            {
                "file": "example.py",
                "lines_of_code": 5,
                "function_count": 1,
                "class_count": 1,
                "import_count": 1,
            },
        )

    def test_source_metrics_reject_invalid_python(self):
        with self.assertRaises(SyntaxError):
            calculate_source_metrics("def broken(:\n    pass\n")


if __name__ == "__main__":
    unittest.main()
