import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.services.investment_sync import InvestmentSyncService

class MockIdentityResolver:
    def get_investment_resources(self, system_id):
        return None

class MockDeveloperManager:
    def find_developer_by_id(self, portal, vendor_id):
        return None
    def get_developer_by_name(self, name):
        return None
    def create_developer_file(self, kwargs):
        pass

def test_prepare_batch_identifiers():
    print("Testing _prepare_batch_identifiers with standard 'vendor_id'...")
    service = InvestmentSyncService(
        identity_resolver=MockIdentityResolver(),
        data_dir=Path("/tmp"),
        public_usi_dir=Path("/tmp"),
        developer_manager=MockDeveloperManager()
    )

    # Mock inputs with standard vendor_id and developer_name
    investments = [
        {
            "url": "https://example.com/test",
            "vendor_id": "999",
            "developer_name": "Test Developer",
            "investment_slug": "test-investment"
        }
    ]

    identifiers, to_process = service._prepare_batch_identifiers("rp", investments)
    assert identifiers == ["https://example.com/test"], f"Failed identifiers: {identifiers}"
    assert to_process[0]["vendor_id"] == "999", "Failed vendor_id extraction"
    assert to_process[0]["dev_slug"] == "rp-999", f"Failed dev_slug creation: {to_process[0]['dev_slug']}"
    assert to_process[0]["inv_slug"] == "test-investment", "Failed inv_slug extraction"
    
    print("test_prepare_batch_identifiers PASSED.")

if __name__ == "__main__":
    test_prepare_batch_identifiers()
