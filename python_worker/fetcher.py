import logging
import time
import json
from datetime import datetime, date
from typing import Optional
from curl_cffi import requests as curl_requests
import requests as std_requests
from .config import SCRAPERAPI_KEY, SCRAPERAPI_LIMIT, USAGE_STATS_PATH

logger = logging.getLogger("Fetcher")

class Fetcher:
    """
    Centralized fetcher for usi-tracker.
    Supports direct requests, impersonation (via curl_cffi), and ScraperAPI fallback.
    """
    
    def __init__(self, scraperapi_key: Optional[str] = None):
        self.scraperapi_key = scraperapi_key or SCRAPERAPI_KEY
        self.session = curl_requests.Session()

    def _get_usage(self):
        """Loads and updates usage stats."""
        if not USAGE_STATS_PATH.exists():
            # Default fallback if file missing
            return {"used": 0, "limit": SCRAPERAPI_LIMIT, "reset_date": "2026-05-11"}
        
        try:
            with open(USAGE_STATS_PATH, "r") as f:
                data = json.load(f)
                stats = data.get("scraperapi", {})
                
                # Check for reset
                reset_date_str = stats.get("reset_date")
                if reset_date_str:
                    reset_date = datetime.strptime(reset_date_str, "%Y-%m-%d").date()
                    if date.today() >= reset_date:
                        logger.info("ScraperAPI reset date reached. Resetting counter.")
                        stats["used"] = 0
                        # Set next reset date (naive +1 month approach)
                        # For simple usage, we just push it 30 days or same day next month
                        new_month = reset_date.month + 1
                        new_year = reset_date.year
                        if new_month > 12:
                            new_month = 1
                            new_year += 1
                        stats["reset_date"] = date(new_year, new_month, reset_date.day).isoformat()
                        self._save_usage(stats)
                return stats
        except Exception as e:
            logger.error(f"Error reading usage stats: {e}")
            return {"used": 0, "limit": SCRAPERAPI_LIMIT, "reset_date": "2026-05-11"}

    def _save_usage(self, stats):
        """Saves usage stats."""
        try:
            USAGE_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(USAGE_STATS_PATH, "r") as f:
                full_data = json.load(f)
            full_data["scraperapi"] = stats
            with open(USAGE_STATS_PATH, "w") as f:
                json.dump(full_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage stats: {e}")

    def fetch(self, url: str, use_impersonate: bool = True, use_scraperapi: bool = True, timeout: int = 30) -> Optional[str]:
        """
        Fetches HTML content from a URL using the best available strategy.
        """
        # Strategy 1: Impersonate (curl_cffi)
        if use_impersonate:
            try:
                logger.info(f"Fetching {url} using impersonation (chrome)")
                # 'chrome' impersonation handles JA3 and common headers
                response = self.session.get(url, impersonate="chrome", timeout=timeout)
                response.raise_for_status()
                logger.info(f"Successfully fetched {url} ({len(response.text)} bytes)")
                return response.text
            except Exception as e:
                logger.warning(f"Impersonate fetch failed for {url}: {e}")
                if not use_scraperapi:
                    return None

        # Strategy 2: ScraperAPI Fallback
        if use_scraperapi and self.scraperapi_key:
            stats = self._get_usage()
            used = stats.get("used", 0)
            limit = stats.get("limit", SCRAPERAPI_LIMIT)
            
            if used >= limit:
                logger.error(f"ScraperAPI limit reached ({used}/{limit}). Skipping fallback.")
                return None

            try:
                logger.info(f"Fetching {url} via ScraperAPI fallback (Usage: {used + 1}/{limit})")
                proxy_url = "http://api.scraperapi.com"
                params = {
                    "api_key": self.scraperapi_key,
                    "url": url,
                    "render": "false" # Try without rendering first
                }
                response = std_requests.get(proxy_url, params=params, timeout=timeout + 30)
                response.raise_for_status()
                
                # Increment usage on success
                stats["used"] = used + 1
                self._save_usage(stats)
                
                return response.text
            except Exception as e:
                logger.error(f"ScraperAPI fallback failed for {url}: {e}")
                
        return None

    def fetch_json(self, url: str, **kwargs) -> Optional[dict]:
        """Fetches and parses JSON from a URL."""
        content = self.fetch(url, **kwargs)
        if content:
            try:
                import json
                return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse JSON from {url}: {e}")
        return None

# Global fetcher instance for easy access
_global_fetcher = Fetcher()

def fetch_html(url: str, **kwargs) -> Optional[str]:
    return _global_fetcher.fetch(url, **kwargs)

def fetch_json(url: str, **kwargs) -> Optional[dict]:
    return _global_fetcher.fetch_json(url, **kwargs)
