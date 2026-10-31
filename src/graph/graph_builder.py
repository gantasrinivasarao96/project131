
from pathlib import Path

from src.graph.dependency_extractor import extract_repository_imports

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


def _is_excluded(path: Path) -> bool:
    """Return True if any path component is an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def _module_names(root: Path, file_path: Path) -> set[str]:
    """Return importable module names for a Python file."""
    relative = file_path.relative_to(root).with_suffix("")
    parts = list(relative.parts)

    if parts[-1] == "__init__":
        parts.pop()

    if not parts:
        return set()

    names = {".".join(parts)}

    # Also support imports that omit the repository's top-level package.
    if len(parts) > 1:
        names.add(".".join(parts[1:]))

    return names


def _resolve_relative_import(
    module_name: str,
    imported_module: str,
    level: int,
) -> str | None:
    """Resolve a relative import to an absolute module name."""
    if level <= 0:
        return imported_module

    package_parts = module_name.split(".")
    if package_parts and package_parts[-1] == "__init__":
        package_parts.pop()
    else:
        package_parts.pop()

    remove_count = level - 1
    if remove_count > len(package_parts):
        return None

    if remove_count:
        package_parts = package_parts[:-remove_count]

    if imported_module:
        package_parts.extend(imported_module.split("."))

    return ".".join(package_parts) or None


def build_dependency_graph(root: Path) -> dict:
    """Build a directed import dependency graph for a Python repository.

    Nodes represent Python files. Edges represent imports between files
    inside the repository. Generated and third-party directories are excluded.
    """
    root = root.resolve()

    # Extract imports, then discard paths from excluded directories.
    imports_by_file = extract_repository_imports(root)
    imports_by_file = {
        relative_path: imports
        for relative_path, imports in imports_by_file.items()
        if not _is_excluded(Path(relative_path))
    }

    module_to_file: dict[str, str] = {}
    for relative_path in sorted(imports_by_file):
        file_path = root / relative_path
        for module_name in _module_names(root, file_path):
            module_to_file[module_name] = relative_path

    nodes = sorted(imports_by_file)
    edges: list[dict[str, str]] = []

    for relative_path in nodes:
        file_path = root / relative_path
        module_names = _module_names(root, file_path)

        for imported in imports_by_file[relative_path]:
            target_module = imported

            # Handle relative imports using the current file's module name.
            for module_name in module_names:
                resolved = _resolve_relative_import(
                    module_name,
                    imported,
                    0,
                )
                if resolved:
                    target_module = resolved
                    break

            target_file = module_to_file.get(target_module)
            if target_file and target_file != relative_path:
                edges.append(
                    {
                        "source": relative_path,
                        "target": target_file,
                    }
                )

    # Deduplicate and sort for deterministic output.
    unique_edges = {
        (edge["source"], edge["target"])
        for edge in edges
    }

    return {
        "nodes": nodes,
        "edges": [
            {"source": source, "target": target}
            for source, target in sorted(unique_edges)
        ],
    }
