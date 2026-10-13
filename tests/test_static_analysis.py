from pathlib import Path

from src.analysis.static_analysis import run_static_analysis


def test_static_analysis():
    results = run_static_analysis(
        Path("data/sample/demo_project")
    )

    assert results["ruff"]["status"] == "completed", results
    assert results["bandit"]["status"] == "completed", results

    assert isinstance(results["ruff"]["findings"], list)
    assert isinstance(results["bandit"]["findings"], list)

    print("PASS: Static analysis integration verified.")


if __name__ == "__main__":
    test_static_analysis()
