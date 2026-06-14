import sys
file_path = 'python_worker/ui/data.jsx'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """        if (target === 'investments') {
          return { investments: data.data || [], unreviewedCount: data.unreviewedCount || 0, loading: false };
        }"""

new_code = """        if (target === 'investments') {
          return { investments: data.data || [], ratingsMap: data.ratingsMap || {}, unreviewedCount: data.unreviewedCount || 0, loading: false };
        }"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Patched data.jsx!")
else:
    print("Could not find old code in data.jsx.")
