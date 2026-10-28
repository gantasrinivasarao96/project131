from pathlib import Path

from src.graph.dependency_extractor import extract_repository_imports


def _module_names(relative_path: str) -> set[str]:
    """Return importable module names for a repository-relative Python file."""
    path = Path(relative_path)

    if path.name == "__init__.py":
        parts = path.parent.parts
    else:
        parts = path.with_suffix("").parts

    names = set()

    if parts:
        names.add(".".join(parts))

    # Support the common src/package layout:
    # src/package/module.py -> package.module
    if parts and parts[0] == "src" and len(parts) > 1:
        names.add(".".join(parts[1:]))

    return names


def build_dependency_graph(root: Path) -> dict:
    """Build a directed graph from local Python module imports."""
    root = root.resolve()
    imports_by_file = extract_repository_imports(root)
    module_to_file = {}

    for relative_path in imports_by_file:
        for module_name in _module_names(relative_path):
            module_to_file[module_name] = relative_path

    edges = set()

    for source_file, imported_modules in imports_by_file.items():
        for imported_module in imported_modules:
            target_file = module_to_file.get(imported_module)

            if target_file and target_file != source_file:
                edges.add((source_file, target_file))

    return {
        "nodes": sorted(imports_by_file),
        "edges": [
            {"source": source, "target": target}
            for source, target in sorted(edges)
        ],
    }
