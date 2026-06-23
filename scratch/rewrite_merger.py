from pathlib import Path
content = Path('/Volumes/Samsam/claude-py/usi-tracker/python_worker/investment_merger.py').read_text()
# check if _rebuild_master exists
print("_rebuild_master in content:", "_rebuild_master" in content)
