import ast
from pathlib import Path


def calculate_source_metrics(source: str, filename: str = "<memory>") -> dict:
    """Calculate basic code metrics directly from Python source text."""
    tree = ast.parse(source, filename=filename)

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
        "file": Path(filename).name,
        "lines_of_code": len(source.splitlines()),
        "function_count": function_count,
        "class_count": class_count,
        "import_count": import_count,
    }


def calculate_code_metrics(file_path: Path) -> dict:
    """Calculate basic source-code metrics for a Python file."""
    file_path = Path(file_path)
    source = file_path.read_text(encoding="utf-8")

    return calculate_source_metrics(source, filename=str(file_path))
