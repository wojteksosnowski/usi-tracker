import os
import ast
from pathlib import Path

def find_slug_functions(directories):
    results = []
    for d in directories:
        path = Path(d)
        for py_file in path.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    has_slug = False
                    for arg in node.args.args:
                        if 'slug' in arg.arg.lower():
                            has_slug = True
                            break
                    if has_slug:
                        results.append(f"- `{py_file.name}` -> `{node.name}`")
    return results

if __name__ == "__main__":
    dirs_to_check = ["python_worker/services", "python_worker/api"]
    results = find_slug_functions(dirs_to_check)
    with open("slug_usage_report.md", "w", encoding="utf-8") as f:
        f.write("# Raport z użycia slugów w funkcjach\n\n")
        f.write("Poniżej znajduje się lista funkcji, które przyjmują argumenty zawierające słowo 'slug'.\n\n")
        for res in sorted(list(set(results))):
            f.write(res + "\n")
    print("Raport wygenerowany.")
