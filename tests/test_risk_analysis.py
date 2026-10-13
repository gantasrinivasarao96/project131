from src.analysis.risk_analysis import calculate_structural_risk


def test_structural_risk():
    graph = {
        "nodes": [
            "main.py",
            "auth.py",
            "database.py",
            "logging.py",
        ],
        "edges": [
            {"source": "main.py", "target": "auth.py"},
            {"source": "main.py", "target": "database.py"},
            {"source": "main.py", "target": "logging.py"},
            {"source": "auth.py", "target": "database.py"},
        ],
    }

    code_metrics = [
        {
            "file": "main.py",
            "lines_of_code": 40,
        },
        {
            "file": "auth.py",
            "lines_of_code": 50,
        },
        {
            "file": "database.py",
            "lines_of_code": 350,
        },
        {
            "file": "logging.py",
            "lines_of_code": 20,
        },
    ]

    result = calculate_structural_risk(graph, code_metrics)

    assert result["method"] == "rule_based_structural_indicators"
    assert result["finding_count"] == 2

    findings = {
        item["file"]: item
        for item in result["findings"]
    }

    assert "high_out_degree" in [
        item["type"]
        for item in findings["main.py"]["indicators"]
    ]

    assert "large_source_file" in [
        item["type"]
        for item in findings["database.py"]["indicators"]
    ]

    assert result["thresholds"]["large_source_file_lines"] == 300

    print("PASS: Structural risk analysis verified.")


if __name__ == "__main__":
    test_structural_risk()
