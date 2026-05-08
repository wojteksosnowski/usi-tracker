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
USI_DEV_DIR = Path(os.getenv("USI_DEV_DIR", str(DROPBOX_PATH / "Public" / "USIdev")))
USI_DEV_RAW_DIR = USI_DEV_DIR / "raw"

# Ensure directories exist
for d in [USI_DATA_DIR, PUBLIC_USI_DIR, USI_DEV_DIR, USI_DEV_RAW_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        # On some macOS setups, symlinked volumes might throw PermissionError on stat/mkdir
        # We silently skip to allow the rest of the app to function.
        pass

# CSV export from Coda.io
CSV_PATH = DROPBOX_PATH / "reference-data" / "coda" / "USImaster.csv"

# HERE Maps API Key
HERE_API_KEY = os.getenv("HERE_API_KEY", "BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c")

# Otodom discovery URLs
OTODOM_DISCOVERY_URLS = [
    "https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/cala-polska?limit=72&investmentEstateType=FLATS&by=LATEST&direction=DESC&viewType=listing"
]

# RynekPierwotny discovery URLs
RP_DISCOVERY_URLS = [
    "https://rynekpierwotny.pl/api/v2/offers/offer/?s=offer-list&display_type=1&distance=5&for_sale=true&limited_presentation=false&page=1&page_size=100&show_on_listing=true&type=1"
]

# TabelaOfert discovery URLs
TABELA_OFERT_DISCOVERY_URLS = [
    "https://tabelaofert.pl/nowe-mieszkania"
]

# Delay settings for portals (seconds)
FETCH_DELAYS = {
    "otodom.pl": 3.0,
    "rynekpierwotny.pl": 1.0,
    "tabelaofert.pl": 1.0,
    "default": 0.5
}

# Other constants
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
VISIBLE_METADATA_FILE = Path(__file__).parent / "data" / "visible_metadata.json"
