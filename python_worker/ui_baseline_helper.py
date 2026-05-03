import os
import re
import json

def extract_static_baseline(ui_dir):
    baseline = {}
    # Regex to find data-component and style
    # Simplified regex for demonstration; captures data-component="Name" and style={{...}}
    comp_regex = re.compile(r'data-component="([^"]+)"')
    style_regex = re.compile(r'style=\{\{\s*([^}]+)\s*\}\}')

    for root, _, files in os.walk(ui_dir):
        for file in files:
            if file.endswith(('.jsx', '.html')):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find all tags with data-component
                    # This is naive but works for our structured code
                    matches = list(comp_regex.finditer(content))
                    for i, match in enumerate(matches):
                        comp_name = match.group(1)
                        # Look for style attribute near the data-component
                        # We search in a window around the match
                        window = content[max(0, match.start()-200) : min(len(content), match.end()+200)]
                        style_match = style_regex.search(window)
                        
                        style_data = {}
                        if style_match:
                            style_str = style_match.group(1)
                            # Basic parsing of 'key: value, key2: value2'
                            for pair in style_str.split(','):
                                if ':' in pair:
                                    k, v = pair.split(':', 1)
                                    style_data[k.strip()] = v.strip().strip("'").strip('"')
                        
                        baseline[f"{comp_name}_{i}_{file}"] = {
                            "component": comp_name,
                            "file": file,
                            "static_styles": style_data
                        }
    
    return baseline

if __name__ == "__main__":
    ui_path = "python_worker/ui"
    baseline = extract_static_baseline(ui_path)
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/visual-baseline-static.json", "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Static baseline extracted for {len(baseline)} component instances.")
