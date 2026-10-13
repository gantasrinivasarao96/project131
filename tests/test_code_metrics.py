from pathlib import Path

from src.analysis.code_metrics import calculate_code_metrics


def test_sample_code_metrics():
    metrics = calculate_code_metrics(
        Path("data/sample/demo_project/auth.py")
    )

    assert metrics["file"] == "auth.py"
    assert metrics["function_count"] == 1
    assert metrics["class_count"] == 0
    assert metrics["import_count"] == 1
    assert metrics["lines_of_code"] > 0

    print("PASS: Code metrics verified.")


if __name__ == "__main__":
    test_sample_code_metrics()
