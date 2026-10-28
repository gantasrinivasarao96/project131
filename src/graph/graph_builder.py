from pathlib import Path

from src.graph.dependency_extractor import extract_repository_imports


def _module_names(relative_path: str) -> set[str]:
    """Return importable module names for a repository-relative file."""
    path = Path(relative_path)

    if path.name == "__init__.py":
        parts = path.parent.parts
    else:
        parts = path.with_suffix("").parts

    names = set()

    if parts:
        names.add(".".join(parts))

    if parts and parts[0] == "src" and len(parts) > 1:
        names.add(".".join(parts[1:]))

    return names


def _resolve_relative_import(
    source_file: str,
    imported_module: str,
) -> str | None:
    """Resolve a relative import to its package-qualified module name."""
    if not imported_module.startswith("."):
        return imported_module

    path = Path(source_file)

    if path.name == "__init__.py":
        package_parts = list(path.parent.parts)
    else:
        package_parts = list(path.with_suffix("").parts[:-1])

    if package_parts and package_parts[0] == "src":
        package_parts = package_parts[1:]

    level = len(imported_module) - len(imported_module.lstrip("."))
    module_tail = imported_module[level:]

    if level > len(package_parts):
        return None

    if level > 1:
        package_parts = package_parts[:-(level - 1)]

    if module_tail:
        package_parts.extend(module_tail.split("."))

    return ".".join(package_parts) or None


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
        resolved_targets = []

        for imported_module in imported_modules:
            resolved_module = _resolve_relative_import(
                source_file, imported_module
            )
            if resolved_module is None:
                continue

            target_file = module_to_file.get(resolved_module)

            if target_file and target_file != source_file:
                resolved_targets.append((resolved_module, target_file))

        for module_name, target_file in resolved_targets:
            target_is_package_init = (
                Path(target_file).name == "__init__.py"
            )

            has_more_specific_module = any(
                other_name.startswith(module_name + ".")
                and other_file != target_file
                and Path(other_file).name != "__init__.py"
                for other_name, other_file in resolved_targets
            )

            if target_is_package_init and has_more_specific_module:
                continue

            edges.add((source_file, target_file))

    return {
        "nodes": sorted(imports_by_file),
        "edges": [
            {"source": source, "target": target}
            for source, target in sorted(edges)
        ],
    }
