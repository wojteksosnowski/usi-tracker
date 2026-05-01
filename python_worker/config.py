import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ScraperAPI Settings
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_LIMIT = 1000
USAGE_STATS_PATH = Path(__file__).parent / "data" / "usage.json"

# Dropbox Root Path
# Defaults to current directory if not set in .env
if not os.getenv("DROPBOX_PATH") and not os.getenv("USI_DATA_DIR"):
    warnings.warn(
        "Neither DROPBOX_PATH nor USI_DATA_DIR env var set, defaulting to '.'. "
        "Set them in .env for correct operation.",
        stacklevel=2,
    )
DROPBOX_PATH = Path(os.getenv("DROPBOX_PATH", "."))

# Paths for Public/USIdata and Public/USI
# Can be overridden individually in .env
USI_DATA_DIR = Path(os.getenv("USI_DATA_DIR", str(DROPBOX_PATH / "Public" / "USIdata")))
PUBLIC_USI_DIR = Path(os.getenv("PUBLIC_USI_DIR", str(DROPBOX_PATH / "Public" / "USI")))

# Ensure directories exist
USI_DATA_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_USI_DIR.mkdir(parents=True, exist_ok=True)

# CSV export from Coda.io
CSV_PATH = DROPBOX_PATH / "reference-data" / "coda" / "USImaster.csv"

# HERE Maps API Key
HERE_API_KEY = os.getenv("HERE_API_KEY", "BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c")

# Other constants
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
