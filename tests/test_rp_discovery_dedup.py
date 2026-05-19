import logging
from unittest.mock import patch, MagicMock
from python_worker.portal_matcher import filter_new_investments

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestRpDedup")

def test_rp_multi_stage_dedup():
    logger.info("Testing RP multi-stage deduplication...")
    
    # Mock discovered items: 2 stages of the same investment
    discovered = [
        {"id": "1001", "name": "Inwestycja X - Etap 1"},
        {"id": "1002", "name": "Inwestycja X - Etap 2"},
    ]
    
    # Mock existing identifiers: only Stage 1 is in DB
    mock_identifiers = {
        "rp_ids": {"1001"},
        "oto_ids": set(),
        "oto_slugs": set()
    }
    
    with patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers", return_value=mock_identifiers):
        filtered = filter_new_investments(discovered, "rp")
        
        # Verify
        stage1 = next(item for item in filtered if item["id"] == "1001")
        stage2 = next(item for item in filtered if item["id"] == "1002")
        
        logger.info(f"Stage 1 (ID 1001) - is_new: {stage1['is_new']}")
        logger.info(f"Stage 2 (ID 1002) - is_new: {stage2['is_new']}")
        
        assert stage1["is_new"] is False, "Stage 1 should be flagged as existing"
        assert stage2["is_new"] is True, "Stage 2 should be flagged as new"
        
        logger.info("RP Multi-stage deduplication test PASSED")

if __name__ == "__main__":
    test_rp_multi_stage_dedup()
