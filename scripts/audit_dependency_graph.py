import argparse
import ast
import json
from pathlib import Path


def module_names(relative_path):
    path = Path(relative_path)
    parts = (
        path.parent.parts
        if path.name == "__init__.py"
        else path.with_suffix("").parts
    )

    names = {".".join(parts)} if parts else set()

    if len(parts) > 1 and parts[0] == "src":
        names.add(".".join(parts[1:]))

    return names


def resolve_import(source, imported):
    if not imported.startswith("."):
        return imported

    path = Path(source)
    package = list(path.parent.parts)

    if package and package[0] == "src":
        package = package[1:]

    level = len(imported) - len(imported.lstrip("."))
    tail = imported[level:]

    if level > len(package):
        return None

    if level > 1:
        package = package[: -(level - 1)]

    if tail:
        package.extend(tail.split("."))

    return ".".join(package) or None


def main():
    parser = argparse.ArgumentParser(
        description="Compare repository imports with a Project 131 graph report."
    )
    parser.add_argument(
        "repository",
        type=Path,
        help="Path to the Python repository being audited",
    )
    parser.add_argument(
        "report",
        type=Path,
        help="Path to the Project 131 JSON report",
    )
    args = parser.parse_args()

    repo = args.repository.resolve()
    report_path = args.report.resolve()

    if not repo.is_dir():
        parser.error(f"Repository directory not found: {repo}")

    if not report_path.is_file():
        parser.error(f"Report file not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    actual = {
        (edge["source"], edge["target"])
        for edge in report["dependency_graph"]["edges"]
    }

    files = sorted(repo.rglob("*.py"))
    module_to_file = {}

    for path in files:
        rel = path.relative_to(repo).as_posix()
        for name in module_names(rel):
            module_to_file[name] = rel

    expected = set()
    ambiguous = []
    parse_errors = []

    for path in files:
        source = path.relative_to(repo).as_posix()

        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=source,
            )
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            parse_errors.append((source, str(exc)))
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = module_to_file.get(alias.name)
                    if target and target != source:
                        expected.add((source, target))
                continue

            if not isinstance(node, ast.ImportFrom):
                continue

            base = "." * node.level + (node.module or "")
            resolved_base = resolve_import(source, base) if base else None
            base_target = module_to_file.get(resolved_base)

            alias_targets = []
            for alias in node.names:
                if alias.name == "*":
                    continue

                candidate = (
                    f"{resolved_base}.{alias.name}"
                    if resolved_base
                    else None
                )
                target = module_to_file.get(candidate) if candidate else None

                if target and target != source:
                    alias_targets.append(target)

            if alias_targets:
                for target in alias_targets:
                    expected.add((source, target))
            elif base_target and base_target != source:
                expected.add((source, base_target))
            elif resolved_base and resolved_base.split(".")[0] in {
                "requests", "tests", "docs"
            }:
                ambiguous.append((source, base, resolved_base))

    missing = expected - actual
    extra = actual - expected

    print("Repository:", repo.name)
    print("Report edges:", len(actual))
    print("Independent direct-module candidates:", len(expected))
    print("Candidate edges absent from report:", len(missing))
    print("Report edges not matched by audit:", len(extra))
    print("Ambiguous package imports:", len(ambiguous))
    print("Audit parse errors:", len(parse_errors))

    print("\nCANDIDATE EDGES ABSENT FROM REPORT (first 20)")
    for source, target in sorted(missing)[:20]:
        print(f"  {source} -> {target}")

    print("\nREPORT EDGES NOT MATCHED BY AUDIT (first 20)")
    for source, target in sorted(extra)[:20]:
        print(f"  {source} -> {target}")

    print("\nAMBIGUOUS IMPORTS (first 20)")
    for source, imported, resolved in ambiguous[:20]:
        print(f"  {source}: {imported!r} -> {resolved!r}")

    print("\nDiagnostic only: this is not a precision/recall measurement.")
    print("Review ambiguous imports and package re-exports manually.")


if __name__ == "__main__":
    main()
