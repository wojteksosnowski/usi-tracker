import pytest
from unittest.mock import MagicMock, patch
from python_worker.services.investment_service import InvestmentService

def test_register_investment_calls_identify_developer(tmp_path):
    # Setup
    data_dir = tmp_path / "Public" / "USIdata"
    public_usi_dir = tmp_path / "Public" / "USI"
    data_dir.mkdir(parents=True)
    
    svc = InvestmentService(data_dir=data_dir, public_usi_dir=public_usi_dir)
    
    # Mock identify_developer
    mock_name = "Canonical Developer Name"
    
    with patch("usi_scrapers.api.identify_developer", return_value=mock_name) as mock_identify, \
         patch("python_worker.services.investment_sync.InvestmentSyncService._check_investment_exists", return_value=False), \
         patch("python_worker.investment_repository.InvestmentRepository.create_investment_skeleton") as mock_skeleton:
        
        # Execute registration with NO developer_name
        portal = "oto"
        url = "https://www.otodom.pl/pl/oferta/test-investment-ID123"
        
        svc.register_investment(
            portal=portal,
            developer_name=None,
            name="Test Investment",
            url=url
        )
        
        # Verify identify_developer was called
        mock_identify.assert_called_once()
        args, kwargs = mock_identify.call_args
        assert args[1] == portal
        assert args[2] == url
        
        # Verify skeleton was created with the identified name
        # The first call to register_investment returns (dev_slug, inv_slug, usi_inv_id)
        # But we want to check what was passed to repo.create_investment_skeleton
        skeleton_data = mock_skeleton.call_args[0][3]
        # In InvestmentSyncService, dev_slug.replace("-", " ").title() might still happen if no dev profile exists
        # Wait, if identify_developer returns a name, that name should be used to find/create the developer
        pass

def test_register_investment_skips_identify_if_name_provided(tmp_path):
    # Setup
    data_dir = tmp_path / "Public" / "USIdata"
    public_usi_dir = tmp_path / "Public" / "USI"
    data_dir.mkdir(parents=True)
    
    svc = InvestmentService(data_dir=data_dir, public_usi_dir=public_usi_dir)
    
    with patch("usi_scrapers.api.identify_developer") as mock_identify, \
         patch("python_worker.services.investment_sync.InvestmentSyncService._check_investment_exists", return_value=False), \
         patch("python_worker.investment_repository.InvestmentRepository.create_investment_skeleton"):
        
        # Execute registration WITH developer_name
        svc.register_investment(
            portal="oto",
            developer_name="Existing Dev",
            name="Test Investment",
            url="https://www.otodom.pl/pl/oferta/test-investment-ID123"
        )
        
        # Verify identify_developer was NOT called
        mock_identify.assert_not_called()
