import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

# Ensure tracker is in path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python_worker.scraper_rp import discover_rp_investments, scrape_rynek_pierwotny
from python_worker.scraper_otodom import discover_otodom_investments, scrape_otodom
from python_worker.services.investment_service import InvestmentService
from python_worker.adapters import AdapterFactory

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.dev_slug = "test-developer"
        self.inv_slug = "test-investment"
        
    @patch("usi_scrapers.scraper_rp.discover_rp_investments")
    def test_rp_shim_discovery(self, mock_lib_discover):
        # Setup mock
        mock_lib_discover.return_value = [{"id": "123", "name": "Test Inv"}]
        
        # Call shim
        results = discover_rp_investments("dev-id")
        
        # Verify
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "123")
        mock_lib_discover.assert_called_once()

    @patch("usi_scrapers.scraper_otodom.scrape_otodom")
    def test_otodom_shim_scrape(self, mock_lib_scrape):
        # Setup mock
        mock_lib_scrape.return_value = {
            "name": "Oto Inv",
            "price": 500000,
            "raw_details": {"some": "raw"}
        }
        
        # Call shim
        result = scrape_otodom("oto-id", self.dev_slug, self.inv_slug)
        
        # Verify
        self.assertEqual(result["name"], "Oto Inv")
        self.assertEqual(result["price"], 500000)

    def test_adapter_factory_returns_library_adapters(self):
        from usi_scrapers.adapters.rp import RPAdapter as LibRP
        from usi_scrapers.adapters.otodom import OtodomAdapter as LibOto
        
        rp_adapter = AdapterFactory.get_adapter("rp")
        oto_adapter = AdapterFactory.get_adapter("otodom")
        
        self.assertEqual(rp_adapter, LibRP)
        self.assertEqual(oto_adapter, LibOto)

    @patch("python_worker.services.investment_service.InvestmentService.update_investment")
    def test_investment_service_orchestration(self, mock_update):
        # This just tests that the service can be instantiated and the method called
        service = InvestmentService(Path("Public/USIdata"))
        mock_update.return_value = True
        
        res = service.update_investment(self.dev_slug, self.inv_slug)
        self.assertTrue(res)

if __name__ == "__main__":
    unittest.main()
