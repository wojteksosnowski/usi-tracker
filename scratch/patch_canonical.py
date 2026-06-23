from pathlib import Path
content = Path('/Volumes/Samsam/claude-py/usi-tracker/CANONICAL.md').read_text()
content = content.replace(
"""│           ├── raw_{portal}_{portal_id}_{YYYYMMDD_HHMMSS}.json   ← Archiwum surowych danych
│           ├── meta_{portal}_{portal_id}.json
│           ├── meta_{portal}_{portal_id}_{YYYYMMDD_HHMMSS}.json  ← Archiwum metadanych z Cody
├── USImaster/                      # W pełni wygenerowane, połączone rekordy T3 (Super-Inwestycje)""", 
"""│           ├── raw_{portal}_{portal_id}_{YYYYMMDD_HHMMSS}.json   ← Archiwum surowych danych
│           ├── meta_{portal}_{portal_id}.json
│           ├── meta_{portal}_{portal_id}_{YYYYMMDD_HHMMSS}.json  ← Archiwum metadanych z Cody
│           ├── usi_stage_stub.json                               ← Placeholder dla etapu wieloetapowego RP
│           └── usi_{portal}_{portal_id}.json                     ← Unified Record (Główny plik produkcyjny)
│
├── USImaster/                      # W pełni wygenerowane, połączone rekordy T3 (Super-Inwestycje)""")
Path('/Volumes/Samsam/claude-py/usi-tracker/CANONICAL.md').write_text(content)
