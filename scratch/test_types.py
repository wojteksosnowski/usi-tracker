targets = [{"identifier": "17702", "target_dir": "dir", "target_image_dir": "img_dir"}]
for i, target in enumerate(targets):
    identifier = target.get("identifier")
    print(f"identifier={identifier}, type={type(identifier)}")
