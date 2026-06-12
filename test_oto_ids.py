import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-tracker")
from python_worker.developer_indexer import get_existing_identifiers
ids = get_existing_identifiers()
oto_ids = ids["oto_ids"]
print(f"Total oto_ids: {len(oto_ids)}")
print(f"Contains 'None'?: {'None' in oto_ids}")
print(f"Contains None?: {None in oto_ids}")
print(f"Contains ''?: {'' in oto_ids}")
