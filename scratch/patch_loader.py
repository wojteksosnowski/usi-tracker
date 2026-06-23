import re
from pathlib import Path

loader_py = Path('/Volumes/Samsam/claude-py/usi-tracker/python_worker/services/investment_loader.py')
content = loader_py.read_text()

# We need to remove the dynamic _load_master_data logic from load_investment
content = re.sub(
    r"# --- NOWA LOGIKA: Łączenie list zdjęć i metadanych dla widoku Master ---.*?# --- Koniec LOGIKI Master ---",
    "",
    content,
    flags=re.DOTALL
)

loader_py.write_text(content)
