from pathlib import Path
from python_worker.api.utils import _load_investment
p = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata/unknown/osiedle-centrum-park-mickiewicza-44-45-legnica-mieszkania-na-sprzedaz/usi_to_9155247.json")
data_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata")
usi_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USI")
res = _load_investment(data_dir=data_dir, public_usi_dir=usi_dir, system_id="to_9155247", usi_file=p, fast_index=True)
print(res)
