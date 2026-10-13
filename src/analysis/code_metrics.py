import ast
from pathlib import Path


def calculate_code_metrics(file_path: Path) -> dict:
    """Calculate basic source-code metrics for a Python file."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    function_count = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )

    class_count = sum(
        isinstance(node, ast.ClassDef)
        for node in ast.walk(tree)
    )

    import_count = sum(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for node in ast.walk(tree)
    )

    return {
        "file": file_path.name,
        "lines_of_code": len(source.splitlines()),
        "function_count": function_count,
        "class_count": class_count,
        "import_count": import_count,
    }
