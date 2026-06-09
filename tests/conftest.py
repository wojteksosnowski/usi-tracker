import pytest

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
