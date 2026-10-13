from pathlib import Path
import json

from src.graph.dependency_extractor import extract_repository_imports


def main():
    root = Path("data/sample/demo_project")
    dependencies = extract_repository_imports(root)

    print("PROJECT 131 - DEPENDENCY EXTRACTION")
    print("=" * 40)
    print(json.dumps(dependencies, indent=2))


if __name__ == "__main__":
    main()
