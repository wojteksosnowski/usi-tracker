import sys
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent.parent  # usi-tracker/ root

# Load .env file from python_worker/ directory (explicit path — CWD-independent)
load_dotenv(Path(__file__).parent / ".env")

# ScraperAPI Settings
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_LIMIT = 1000
USAGE_STATS_PATH = Path(__file__).parent / "data" / "usage.json"

# Add usi-scrapers and usi-crawlers to path if not already there
LIB_PATH = str(_BASE_DIR.parent / "usi-scrapers")
CRAWLERS_PATH = str(_BASE_DIR.parent / "usi-crawlers")
for p in [LIB_PATH, CRAWLERS_PATH]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)
DROPBOX_PATH = Path(os.getenv("DROPBOX_PATH", str(_BASE_DIR)))

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
SEGMENTS_CONFIG_PATH = Path(__file__).parent / "schemas" / "segments.json"

# Cached library instances
_cached_config = None
_cached_tech_manager = None
_cached_fetcher = None

def get_scraper_config():
    """Returns a ScraperConfig object for use with the usi-scrapers library."""
    try:
        import usi_scrapers
        current_version = getattr(usi_scrapers, "__version__", "0.0.0")

        # Allow any 0.9.x version
        if not current_version.startswith("0.9."):
            warnings.warn(
                f"USI Scrapers version mismatch! Expected: 0.9.x, "
                f"Found: {current_version}. Please update the library.",
                stacklevel=2
            )
            
        from usi_scrapers.models import ScraperConfig
        return ScraperConfig(
            public_dir=USI_DATA_DIR.parent, # Public folder containing USIdata and USI
            scraperapi_key=SCRAPERAPI_KEY,
            rp_discovery_urls=RP_DISCOVERY_URLS,
            otodom_discovery_urls=OTODOM_DISCOVERY_URLS,
            to_discovery_urls=TABELA_OFERT_DISCOVERY_URLS
        )
    except ImportError:
        # Fallback if library not in path yet
        return None

def get_shared_config():
    global _cached_config
    if _cached_config is None:
        _cached_config = get_scraper_config()
    return _cached_config

def get_shared_tech_manager():
    global _cached_tech_manager
    config = get_shared_config()
    if _cached_tech_manager is None and config:
        from usi_scrapers.manager import TechnicalDataManager
        _cached_tech_manager = TechnicalDataManager(config)
    return _cached_tech_manager

def get_shared_fetcher():
    global _cached_fetcher
    config = get_shared_config()
    if _cached_fetcher is None and config:
        from usi_scrapers.fetcher import Fetcher
        _cached_fetcher = Fetcher(config)
    return _cached_fetcher
