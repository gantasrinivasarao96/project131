
import ast
import os
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "site-packages",
    "node_modules",
    "build",
    "dist",
}


def extract_imports(file_path: Path) -> set[str]:
    """Extract absolute and relative module import candidates."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level

            if node.module:
                base = prefix + node.module
                imports.add(base)

                for alias in node.names:
                    if alias.name != "*":
                        imports.add(f"{base}.{alias.name}")
            else:
                for alias in node.names:
                    if alias.name != "*":
                        imports.add(prefix + alias.name)

    return imports


def _python_files(root: Path):
    """Yield Python files while pruning excluded directories."""
    for current_dir, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(
            name for name in dir_names if name not in EXCLUDED_DIRS
        )

        for file_name in sorted(file_names):
            if file_name.endswith(".py"):
                yield Path(current_dir) / file_name


def extract_repository_imports(root: Path) -> dict[str, list[str]]:
    """Extract imports from Python files, skipping generated and vendor dirs."""
    root = root.resolve()
    dependencies: dict[str, list[str]] = {}

    for file_path in _python_files(root):
        relative_path = file_path.relative_to(root).as_posix()
        dependencies[relative_path] = sorted(extract_imports(file_path))

    return dependencies
