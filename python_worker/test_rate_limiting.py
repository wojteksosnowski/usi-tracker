import time
import unittest
from unittest.mock import patch, MagicMock
from python_worker.fetcher import Fetcher

class TestRateLimiting(unittest.TestCase):
    def setUp(self):
        # We use a fresh fetcher for each test
        self.fetcher = Fetcher(scraperapi_key="test_key")
        # Mock session.get to avoid real network calls
        self.fetcher.session.get = MagicMock()
        self.fetcher.session.get.return_value.text = "<html></html>"
        self.fetcher.session.get.return_value.status_code = 200

    @patch("python_worker.fetcher.time.sleep")
    @patch("python_worker.fetcher.time.time")
    def test_rate_limit_applied_same_domain(self, mock_time, mock_sleep):
        # Setup: first call at t=100
        mock_time.return_value = 100.0
        domain = "otodom.pl"
        url = f"https://www.{domain}/test"
        
        # First fetch - no sleep expected
        self.fetcher.fetch(url)
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(self.fetcher.last_fetch_times[domain], 100.0)

        # Second fetch at t=101.0 (delay for otodom is 3.0)
        mock_time.return_value = 101.0
        self.fetcher.fetch(url)
        
        # Should sleep for 3.0 - (101.0 - 100.0) = 2.0
        mock_sleep.assert_called_with(2.0)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("python_worker.fetcher.time.sleep")
    @patch("python_worker.fetcher.time.time")
    def test_rate_limit_independent_domains(self, mock_time, mock_sleep):
        # Setup: first call at t=100
        mock_time.return_value = 100.0
        
        # Fetch from domain A
        self.fetcher.fetch("https://otodom.pl/1")
        
        # Fetch from domain B at t=101.0
        mock_time.return_value = 101.0
        self.fetcher.fetch("https://rynekpierwotny.pl/1")
        
        # No sleep should be called because domains are different
        self.assertEqual(mock_sleep.call_count, 0)

    @patch("python_worker.fetcher.time.sleep")
    def test_real_sleep_not_called_for_fast_requests(self, mock_sleep):
        # If enough time has passed, no sleep
        with patch("python_worker.fetcher.time.time") as mock_time:
            mock_time.return_value = 100.0
            self.fetcher.fetch("https://tabelaofert.pl/1")
            
            mock_time.return_value = 110.0 # 10s later
            self.fetcher.fetch("https://tabelaofert.pl/2")
            
            self.assertEqual(mock_sleep.call_count, 0)

if __name__ == "__main__":
    unittest.main()
