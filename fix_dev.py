import json

file_path = "/Volumes/Samsam/Public/USIdev/albero/usi_dev_DEV-28754_albero.json"
with open(file_path, "r") as f:
    data = json.load(f)

if not data.get("portal_mapping"):
    data["portal_mapping"] = {}
data["portal_mapping"]["to"] = {"agency_id": ""}

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("Fixed DEV-28754 mapping!")
