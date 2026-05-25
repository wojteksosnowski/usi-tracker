import re
with open("test_to.html", "r") as f:
    html = f.read()

m = re.search(r'\\?"kryterium\\?"\s*:\s*\\?"([a-zA-Z0-9-]+)\\?"', html)
if m:
    print("MATCH1:", m.group(1))

m2 = re.search(r'\\?"klient\\?"\s*:\s*\{[^}]*?\\?"kryterium\\?"\s*:\s*\\?"([a-zA-Z0-9-]+)\\?"', html)
if m2:
    print("MATCH2:", m2.group(1))
