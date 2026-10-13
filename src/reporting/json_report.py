import json
from pathlib import Path


def save_json_report(report: dict, output_path: Path) -> Path:
    """Save a repository analysis report as formatted JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return output_path
