import json
from python_worker.merger import Merger

oto_data = {"image_urls": ["url1", "url2"]}
merged = Merger.merge(oto=oto_data, existing_data={})
print("merged image_urls:", merged.get("image_urls"))
