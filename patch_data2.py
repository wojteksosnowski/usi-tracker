import sys
file_path = 'python_worker/ui/data.jsx'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """      if (data && typeof data === 'object' && data.data) {
        setVariable('unreviewedCount', data.unreviewedCount || 0);
        return Array.isArray(data.data) ? data.data : [];
      }"""

new_code = """      if (data && typeof data === 'object' && data.data) {
        setVariable('unreviewedCount', data.unreviewedCount || 0);
        if (data.ratingsMap) setVariable('ratingsMap', data.ratingsMap);
        return Array.isArray(data.data) ? data.data : [];
      }"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Patched data.jsx fetch logic!")
else:
    print("Could not find old code in data.jsx.")
