import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from usi_scrapers.models import ScraperConfig
from usi_scrapers.manager import TechnicalDataManager

config = ScraperConfig(public_dir="/Volumes/Samsam/claude-py/usi-tracker/Public")
mgr = TechnicalDataManager(config)
path = mgr.get_investment_path("oto", "4BFOJ")
print(f"Path for 4BFOJ: {path}")

# Wait, the tracker's tech manager is shared!
