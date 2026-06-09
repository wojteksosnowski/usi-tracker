import pytest
import sys
import os
from pathlib import Path

# Add usi-scrapers and usi-crawlers to path
BASE_DIR = Path(__file__).resolve().parent.parent
LIB_PATH = str(BASE_DIR.parent / "usi-scrapers")
CRAWLERS_PATH = str(BASE_DIR.parent / "usi-crawlers")
for p in [LIB_PATH, CRAWLERS_PATH]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

def pytest_configure(config):
    # Initial state: no non-live tests have failed
    config.failed_non_live = False

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Tracks if any non-live test fails."""
    outcome = yield
    rep = outcome.get_result()
    
    # We only care about the actual test call failure
    if rep.when == "call" and rep.failed:
        if "live" not in item.keywords:
            item.config.failed_non_live = True

def pytest_runtest_setup(item):
    """Skips live tests if a preceding non-live test failed."""
    if "live" in item.keywords and getattr(item.config, "failed_non_live", False):
        pytest.skip("Skipping live test because previous non-live tests failed")

def pytest_collection_modifyitems(items):
    """Ensures live tests are executed last."""
    live_items = []
    other_items = []
    for item in items:
        if "live" in item.keywords:
            live_items.append(item)
        else:
            other_items.append(item)
    items[:] = other_items + live_items
