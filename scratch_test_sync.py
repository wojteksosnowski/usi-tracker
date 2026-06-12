import json
from pathlib import Path
import sys
sys.path.insert(0, "/Volumes/Samsam/claude-py/usi-scrapers")

from usi_scrapers import mapping
raw_files = list(Path('Public/USIdata').rglob('raw_oto_*.json'))
if raw_files:
    raw_payload = json.loads(raw_files[0].read_text())
    
    m = mapping.get_mapping("oto")
    dev_id_path = m.get("developer_id")
    print("Dev ID Path in oto:", dev_id_path)
    
    vid = mapping.resolve_path(raw_payload, dev_id_path)
    print("Resolved vid:", vid)
