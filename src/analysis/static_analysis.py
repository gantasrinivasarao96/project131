"""Run static analysis tools on a Python repository."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from src.graph.graph_builder import EXCLUDED_DIRS


def _is_excluded(path: Path) -> bool:
    """Return True if any path component is an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def _run_json_command(command: list[str], tool: str) -> dict:
    """Run a static-analysis tool and parse its JSON output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "findings": [],
            "error": "Analysis exceeded the 120-second time limit.",
        }
    except OSError as exc:
        return {
            "status": "error",
            "findings": [],
            "error": type(exc).__name__,
        }

    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {
            "status": "error",
            "findings": [],
            "error": "Tool did not return valid JSON.",
        }

    if tool == "ruff":
        if not isinstance(data, list):
            return {
                "status": "error",
                "findings": [],
                "error": "Unexpected Ruff JSON format.",
            }
        findings = data
        summary = {"finding_count": len(findings)}

    elif tool == "bandit":
        if not isinstance(data, dict):
            return {
                "status": "error",
                "findings": [],
                "error": "Unexpected Bandit JSON format.",
            }
        findings = data.get("results", [])
        summary = data.get("metrics", {})

    else:
        return {
            "status": "error",
            "findings": [],
            "error": "Unsupported analysis tool.",
        }

    return {
        "status": "completed" if result.returncode in (0, 1) else "error",
        "exit_code": result.returncode,
        "findings": findings,
        "summary": summary,
    }


def run_static_analysis(root: Path) -> dict:
    """Run available Ruff and Bandit checks on repository Python files."""
    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository directory not found: {root}"
        )

    python_files = sorted(
        path
        for path in root.rglob("*.py")
        if not _is_excluded(path.relative_to(root))
    )

    if not python_files:
        return {
            "ruff": {"status": "not_applicable", "findings": []},
            "bandit": {"status": "not_applicable", "findings": []},
        }

    file_args = [str(path) for path in python_files]
    results = {}

    environment_bin = Path(sys.prefix) / "bin"

    ruff_candidate = environment_bin / "ruff"
    ruff_executable = (
        str(ruff_candidate)
        if ruff_candidate.is_file()
        else shutil.which("ruff")
    )

    if ruff_executable:
        results["ruff"] = _run_json_command(
            [
                ruff_executable,
                "check",
                "--output-format=json",
                *file_args,
            ],
            "ruff",
        )
    else:
        results["ruff"] = {
            "status": "unavailable",
            "findings": [],
        }

    bandit_candidate = environment_bin / "bandit"
    bandit_executable = (
        str(bandit_candidate)
        if bandit_candidate.is_file()
        else shutil.which("bandit")
    )

    if bandit_executable:
        results["bandit"] = _run_json_command(
            [
                bandit_executable,
                "-f",
                "json",
                *file_args,
            ],
            "bandit",
        )
    else:
        results["bandit"] = {
            "status": "unavailable",
            "findings": [],
        }

    return results
