import sys
from pathlib import Path
import json

# Add virtual environment site-packages just in case
try:
    import usi_scrapers
    from usi_scrapers.api import get_scraper_func
    from usi_scrapers.manager import TechnicalDataManager
    from usi_scrapers.models import ScraperConfig
    
    print(f"✅ Library loaded successfully: {usi_scrapers.__file__}")
    
    func = get_scraper_func("rp", "discover")
    print(f"✅ API get_scraper_func works. Func found: {func.__name__ if func else None}")
    
    config = ScraperConfig(public_dir=Path("Public"))
    tdm = TechnicalDataManager(config)
    print(f"✅ TechnicalDataManager instantiated. Image path: {tdm.get_image_path('dev', 'inv')}")
    
except Exception as e:
    print(f"❌ Error loading library: {e}")
    sys.exit(1)
