from pathlib import Path

from src.graph.dependency_extractor import extract_repository_imports


def build_dependency_graph(root: Path) -> dict:
    """Build a directed graph from local Python module imports."""
    root = root.resolve()
    imports_by_file = extract_repository_imports(root)

    module_to_file = {}

    for relative_path in imports_by_file:
        path = Path(relative_path)

        if path.name == "__init__.py":
            module_name = ".".join(path.parent.parts)
        else:
            module_name = ".".join(path.with_suffix("").parts)

        if module_name:
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
