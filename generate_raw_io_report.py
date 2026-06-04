import os
import ast
from pathlib import Path

def find_io_functions(directories):
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
                    has_io = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            func = child.func
                            if isinstance(func, ast.Name):
                                if func.id == "open":
                                    has_io = True
                                    break
                            elif isinstance(func, ast.Attribute):
                                if func.attr in ("write_text", "write_bytes", "write", "dump"):
                                    has_io = True
                                    break
                    if has_io:
                        results.append(f"- `{py_file.name}` -> `{node.name}`")
    return results

if __name__ == "__main__":
    dirs_to_check = ["python_worker/services", "python_worker/api"]
    results = find_io_functions(dirs_to_check)
    with open("raw_io_usage_report.md", "w", encoding="utf-8") as f:
        f.write("# Raport z operacji I/O (zapis na dysk) w funkcjach\n\n")
        f.write("Poniżej znajduje się lista funkcji, które prawdopodobnie wykonują zapis na dysk (np. używają `open`, `write_text`, `json.dump`).\n\n")
        for res in sorted(list(set(results))):
            f.write(res + "\n")
    print("Raport wygenerowany.")
