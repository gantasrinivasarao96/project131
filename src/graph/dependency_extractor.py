import ast
from pathlib import Path


def extract_imports(file_path: Path) -> set[str]:
    """Extract imported module names from a Python source file."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return imports


def extract_repository_imports(root: Path) -> dict[str, list[str]]:
    """Extract imports for every Python file under a repository."""
    root = root.resolve()
    dependencies = {}

    for file_path in sorted(root.rglob("*.py")):
        relative_path = file_path.relative_to(root).as_posix()
        dependencies[relative_path] = sorted(extract_imports(file_path))

    return dependencies
