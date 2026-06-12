import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from usi_scrapers.utils.portals import portal_url

print(portal_url("oto", "investment", full_slug=None))
