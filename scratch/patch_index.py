from pathlib import Path
import json

index_py = Path('/Volumes/Samsam/claude-py/usi-tracker/python_worker/investment_index.py')
content = index_py.read_text()

# We need to update _load_from_disk to scan USImaster and remove is_grouped

# First, modify the scanning directory to also include USImaster
import re

# Remove master_to_primary mapping completely since we don't use it anymore
content = re.sub(
    r"master_to_primary = {}\s+try:.*?(?=\n\s+# 3\. Główne pętla)",
    "",
    content,
    flags=re.DOTALL
)

# Modify the scanning logic
new_scan_logic = """        # 3. Główne pętla po plikach usi_*.json (USIdata + USImaster)
        import itertools
        from python_worker.config import PUBLIC_DIR
        master_dir = PUBLIC_DIR / "USImaster"
        scan_iters = [self.data_dir.rglob("usi_*.json")]
        if master_dir.exists():
            scan_iters.append(master_dir.rglob("usi_*.json"))
            
        for usi_file in itertools.chain(*scan_iters):"""
        
content = re.sub(
    r"\s+# 3\. Główne pętla po plikach usi_\*\.json.*?(?=for usi_file in self\.data_dir\.rglob\(\"usi_\*\.json\"\):)",
    "\n" + new_scan_logic + "\n        ",
    content,
    flags=re.DOTALL
)

# Replace the loop iteration
content = content.replace('for usi_file in self.data_dir.rglob("usi_*.json"):', '')

# Remove is_grouped logic
content = re.sub(
    r"\s+master_id = data\.get\(\"master_id\"\).*?entry\[\"is_grouped\"\] = is_grouped",
    "",
    content,
    flags=re.DOTALL
)

# And in add_or_update
content = re.sub(
    r"is_grouped = False\s+if master_id:.*?entry\[\"is_grouped\"\] = is_grouped",
    "",
    content,
    flags=re.DOTALL
)

index_py.write_text(content)
