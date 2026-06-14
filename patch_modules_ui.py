import sys
file_path = 'python_worker/ui/modules/modules-ui.jsx'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """          const indexInv = fastIndex[i.usi_inv_id || i.id];
          const ratings = (indexInv && indexInv.ratings) ? indexInv.ratings : (i.ratings || {});"""

new_code = """          const indexInv = fastIndex[i.usi_inv_id || i.id];
          let ratings = (indexInv && indexInv.ratings) ? indexInv.ratings : null;
          if (!ratings && bus && bus.ratingsMap) {
            ratings = bus.ratingsMap[i.usi_inv_id || i.id];
          }
          if (!ratings) {
            ratings = (i.ratings || {});
          }"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Patched modules-ui.jsx!")
else:
    print("Could not find old code in modules-ui.jsx.")
