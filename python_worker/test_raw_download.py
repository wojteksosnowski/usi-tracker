import logging
from python_worker.scraper_rp import download_raw_rp_json
from python_worker.scraper_otodom import download_raw_otodom_json
from python_worker.scraper_to import download_raw_to_json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestRawDownload")

def test_downloads():
    # 1. RynekPierwotny
    logger.info("Testing RP raw download...")
    rp_path = download_raw_rp_json("14563", "test-dev", "rp-test-inv")
    if rp_path and rp_path.exists():
        logger.info(f"RP Download SUCCESS: {rp_path}")
    else:
        logger.error("RP Download FAILED")

    # 2. Otodom
    logger.info("Testing Otodom raw download...")
    oto_url = "https://www.otodom.pl/pl/inwestycja/mickiewicza-21-residence-ID4B9JX"
    oto_path = download_raw_otodom_json(oto_url, "test-dev", "oto-test-inv")
    if oto_path and oto_path.exists():
        logger.info(f"Otodom Download SUCCESS: {oto_path}")
    else:
        logger.error("Otodom Download FAILED")

    # 3. TabelaOfert
    logger.info("Testing TabelaOfert raw download...")
    to_url = "https://tabelaofert.pl/inwestycja/nowe-miasto-polesie-iv-pienista-lodz-polesie-mieszkania-na-sprzedaz,i8978722"
    to_path = download_raw_to_json(to_url, "test-dev", "to-test-inv")
    if to_path and to_path.exists():
        logger.info(f"TO Download SUCCESS: {to_path}")
    else:
        logger.error("TO Download FAILED")

    # 4. Test Archiving
    logger.info("Testing archiving by re-downloading RP...")
    rp_path_2 = download_raw_rp_json("14563", "test-dev", "rp-test-inv")
    # Check if there is a file with timestamp in the directory
    files = list(rp_path_2.parent.glob("raw_rp_rp-test-inv_*.json"))
    if files:
        logger.info(f"Archiving SUCCESS. Found {len(files)} archived files.")
    else:
        logger.error("Archiving FAILED")

if __name__ == "__main__":
    test_downloads()
