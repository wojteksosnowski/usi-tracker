import os
import json
import shutil
import logging
from pathlib import Path
from python_worker.services.investment_service import InvestmentService
from python_worker import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StabilityTest")

# Test data: Known active URLs
TEST_CASES = [
    {
        "portal": "rp",
        "name": "Wzgórze Markowca",
        "dev_slug": "euro-styl-s-a",
        "inv_slug": "wzgorze-markowca-rumia",
        "id": "20327",
        "url": "https://rynekpierwotny.pl/oferty/euro-styl-sa/wzgorze-markowca-rumia-20327/"
    },
    {
        "portal": "oto",
        "name": "Nowe Inwestycje (active)",
        "dev_slug": "deweloper",
        "inv_slug": "inwestycja-test",
        "url": "https://www.otodom.pl/pl/oferta/nowoczesny-dom-wolnostojacy-w-stanie-deweloperskim-ID4q7H0"
    }
]

def run_stability_test():
    # 1. Setup isolated environment
    test_root = Path("temp_test_run")
    if test_root.exists():
        shutil.rmtree(test_root)
    
    test_data_dir = test_root / "USIdata"
    test_usi_dir = test_root / "USI"
    test_data_dir.mkdir(parents=True)
    test_usi_dir.mkdir(parents=True)
    
    # 2. PATCH CONFIG GLOBALLY
    config.USI_DATA_DIR = test_data_dir
    config.PUBLIC_USI_DIR = test_usi_dir
    
    logger.info(f"🚀 Starting stability test in: {test_root.absolute()}")
    
    service = InvestmentService(data_dir=test_data_dir, public_usi_dir=test_usi_dir)
    results = []

    # 3. Process test cases
    for case in TEST_CASES:
        logger.info(f"--- Testing Portal: {case['portal'].upper()} ({case['name']}) ---")
        try:
            # Registration process
            service.register_investment(
                case['portal'],
                case['dev_slug'],
                case['inv_slug'],
                case['name'],
                item_id=case.get('id'),
                url=case['url']
            )
            
            # Synchronous update
            success = service.update_investment(case['dev_slug'], case['inv_slug'])
            
            if not success:
                logger.error(f"❌ Failed to sync {case['name']}")
                results.append({"case": case['name'], "status": "FAIL", "reason": "Sync returned False"})
                continue
                
            # Verify results on disk
            inv_dir = test_data_dir / case['dev_slug'] / case['inv_slug']
            usi_json_path = inv_dir / f"usi_{case['inv_slug']}.json"
            raw_json_path = inv_dir / f"raw_{case['portal']}_{case['inv_slug']}.json"
            img_dir = test_usi_dir / case['dev_slug'] / case['inv_slug']
            
            report = {
                "case": case['name'],
                "portal": case['portal'],
                "usi_json": usi_json_path.exists(),
                "raw_json": raw_json_path.exists(),
                "images_saved": 0,
                "metadata_ok": False,
                "price_ok": False,
                "status": "FAIL"
            }
            
            if usi_json_path.exists():
                with open(usi_json_path, "r") as f:
                    data = json.load(f)
                    
                # Check critical metadata
                has_name = bool(data.get("name"))
                has_coords = bool(data.get("location", {}).get("coords") and data["location"]["coords"][0])
                fin = data.get("financials", {})
                has_price = (fin.get("price_min") is not None and fin["price_min"] > 0) or \
                            (fin.get("price_avg") is not None and fin["price_avg"] > 0)
                
                report["metadata_ok"] = has_name and has_coords
                report["price_ok"] = has_price
                
                if img_dir.exists():
                    img_files = [p for p in img_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
                    report["images_saved"] = len(img_files)
                
                if report["usi_json"] and report["raw_json"] and report["metadata_ok"] and report["images_saved"] > 0:
                    report["status"] = "PASS"
                    logger.info(f"✅ {case['name']} passed stability check.")
                else:
                    logger.warning(f"⚠️ {case['name']} incomplete: JSON={report['usi_json']}, Raw={report['raw_json']}, Meta={report['metadata_ok']}, Imgs={report['images_saved']}, Price={report.get('price_ok')}")
            
            results.append(report)
            
        except Exception as e:
            logger.exception(f"💥 Exception during test of {case['name']}")
            results.append({"case": case['name'], "status": "ERROR", "reason": str(e)})

    # 4. Final Summary
    logger.info("\n" + "="*50)
    logger.info("FINAL STABILITY REPORT")
    logger.info("="*50)
    all_passed = True
    for r in results:
        status_icon = "✅" if r["status"] == "PASS" else "❌"
        logger.info(f"{status_icon} {r['case']} ({r.get('portal', '??')}): {r['status']}")
        if r["status"] != "PASS":
            all_passed = False
            
    if all_passed:
        logger.info("\n✨ ALL PORTALS STABLE ✨")
    else:
        logger.error("\n🛑 STABILITY REGRESSION DETECTED 🛑")

    return results

if __name__ == "__main__":
    run_stability_test()
