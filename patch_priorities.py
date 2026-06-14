import re

file_path = "python_worker/services/investment_sync.py"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace(
    '"rp": ["id", "url"]',
    '"rp": ["url", "id"]'
).replace(
    '"oto": ["id", "url"]',
    '"oto": ["url", "id"]'
).replace(
    '"to": ["id", "url"]',
    '"to": ["url", "id"]'
)

with open(file_path, "w") as f:
    f.write(content)

print("Patch applied to investment_sync.py!")
