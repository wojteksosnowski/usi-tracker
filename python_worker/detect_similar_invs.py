import json
import logging
import argparse
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR, PUBLIC_USI_DIR
from python_worker.developer_manager import DeveloperManager
import python_worker.investment_index as inv_index

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def detect_similar_invs(data_dir: Path, target_dev_slug: str = None, target_inv_id: str = None, target_inv_slug: str = None):
    """
    Detects similar investments based on location bounds, delivery date, and units count.
    Can be scoped to a single developer's "umbrella", a single investment by ID, or by slug.
    """
    dm = DeveloperManager(data_dir, Path(USI_DEV_DIR))
    all_invs = inv_index.load(data_dir) or []

    if not all_invs:
        logger.warning("Investment index is empty.")
        return

    # We look up dev_masters on the fly because list_developers() excludes children.
    dev_masters_cache = {} # cache to avoid repeated file reads
    
    # Also load the central dismissed cache for investments
    dismissed_cache = {}
    central = data_dir / "dismissed_inv_pairs.jsonl"
    if central.exists():
        for line in central.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                dismisser = e.get("dismisser_id")
                dismissed = e.get("dismissed_id")
                if dismisser and dismissed:
                    dismissed_cache.setdefault(dismisser, set()).add(dismissed)
            except Exception:
                continue

    target_inv = None
    if target_inv_id:
        target_inv = next((i for i in all_invs if i.get("usi_inv_id") == target_inv_id), None)
    elif target_inv_slug and target_dev_slug:
        target_inv = next((i for i in all_invs if i.get("slug") == f"{target_dev_slug}/{target_inv_slug}"), None)

    target_invs = []
    if target_inv:
        target_invs = [target_inv]
    elif target_dev_slug and not target_inv_slug:
        target_invs = [i for i in all_invs if i.get("developer_slug") == target_dev_slug and not i.get("master_id")]
    else:
        target_invs = [i for i in all_invs if not i.get("master_id")]

    all_invs_for_comparison = [i for i in all_invs if not i.get("master_id")]

    suggestions_count = 0

    for inv1 in target_invs:
                
            inv1_id = inv1.get("usi_inv_id") or inv1.get("slug") # Fallback to slug if no ID
            if not inv1_id: continue
            
            c1 = inv1.get("coords", [0, 0])
            u1 = inv1.get("units") or 0
            d1 = inv1.get("specifications", {}).get("delivery_year")
            q1 = inv1.get("specifications", {}).get("delivery_quarter")
            
            if not c1 or not c1[0]: continue
            
            new_suggestions = []
            
            for inv2 in all_invs_for_comparison:
                if inv1 is inv2: continue
                inv2_id = inv2.get("usi_inv_id") or inv2.get("slug")
                if not inv2_id: continue
                
                # Check dismissed
                if inv2_id in dismissed_cache.get(inv1_id, set()) or inv1_id in dismissed_cache.get(inv2_id, set()):
                    continue
                
                c2 = inv2.get("coords", [0, 0])
                u2 = inv2.get("units") or 0
                
                # Try to extract year/quarter from delivery_date if missing
                def _get_yq(inv):
                    specs = inv.get("specifications", {})
                    y = specs.get("delivery_year")
                    q = specs.get("delivery_quarter")
                    date_str = specs.get("delivery_date", "")
                    
                    if not y and date_str and len(date_str) >= 4 and date_str[:4].isdigit():
                        y = int(date_str[:4])
                    if not q and date_str:
                        if "-Q" in date_str:
                            try: q = int(date_str.split("-Q")[1])
                            except: pass
                        elif len(date_str) >= 7 and date_str[5:7].isdigit():
                            m = int(date_str[5:7])
                            q = (m - 1) // 3 + 1
                    return y, q
                
                d1, q1 = _get_yq(inv1)
                d2, q2 = _get_yq(inv2)
                
                if not c2 or not c2[0]: continue
                
                # Location bounds check (~3rd decimal place is ~110m)
                lat_diff = abs(c1[0] - c2[0])
                lon_diff = abs(c1[1] - c2[1])
                
                if lat_diff > 0.005 or lon_diff > 0.005:
                    continue
                    
                score = 0.0
                reasons = []
                
                # Name check
                name1 = (inv1.get("name") or "").strip().lower()
                name2 = (inv2.get("name") or "").strip().lower()
                if name1 and name2 and name1 == name2:
                    score += 0.4
                    reasons.append("Identyczna nazwa inwestycji")
                    
                # Developer similarity check
                dev1 = (inv1.get("developer") or "").strip().lower()
                dev2 = (inv2.get("developer") or "").strip().lower()
                if dev1 and dev2 and (dev1 in dev2 or dev2 in dev1):
                    score += 0.2
                    reasons.append("Zbliżony deweloper")
                
                if round(c1[0], 3) == round(c2[0], 3) and round(c1[1], 3) == round(c2[1], 3):
                    score += 0.4
                    reasons.append("Bardzo bliska geolokalizacja")
                elif lat_diff < 0.005 and lon_diff < 0.005:
                    score += 0.2
                    reasons.append("Zbliżona geolokalizacja")
                    
                # Delivery check
                if d1 and d2:
                    if d1 == d2 and q1 == q2:
                        score += 0.3
                        reasons.append("Ten sam kwartał oddania")
                    elif d1 == d2:
                        score += 0.2
                        reasons.append("Ten sam rok oddania")
                    elif abs((d1*4 + (q1 or 1)) - (d2*4 + (q2 or 1))) <= 1:
                        score += 0.15
                        reasons.append("Różnica 1 kwartału w oddaniu")
                        
                # Units check
                if u1 and u2:
                    if u1 == u2:
                        score += 0.3
                        reasons.append("Identyczna liczba mieszkań")
                    elif abs(u1 - u2) <= 3:
                        score += 0.2
                        reasons.append(f"Zbieżna liczba mieszkań ({u1} vs {u2})")
                
                if score >= 0.7:
                    new_suggestions.append({
                        "usi_inv_id": inv2.get("usi_inv_id"), # might be None, but handled below
                        "developer_slug": inv2.get("developer_slug"),
                        "investment_slug": inv2.get("investment_slug"),
                        "name": inv2.get("name"),
                        "reason": ", ".join(reasons),
                        "score": round(score, 2)
                    })
            
            if new_suggestions:
                # Save suggestions to inv1
                from python_worker.services.investment_service import InvestmentService
                svc = InvestmentService(data_dir=data_dir)
                resources = svc.get_investment_resources(inv1_id)
                usi_file = resources["files"].get("anchor") if resources else None
                
                if usi_file:
                    with open(usi_file, "r", encoding="utf-8") as f:
                        inv_data = json.load(f)
                    
                    existing = inv_data.get("suggestions", [])
                    # Merge new with existing
                    existing_keys = {s.get("usi_inv_id") or f"{s.get('developer_slug')}/{s.get('investment_slug')}" for s in existing}
                    added = False
                    for ns in new_suggestions:
                        ns_key = ns.get("usi_inv_id") or f"{ns.get('developer_slug')}/{ns.get('investment_slug')}"
                        if ns_key not in existing_keys:
                            existing.append(ns)
                            added = True
                            
                    if added:
                        inv_data["suggestions"] = existing
                        with open(usi_file, "w", encoding="utf-8") as f:
                            json.dump(inv_data, f, indent=2, ensure_ascii=False)
                        inv_index.upsert(data_dir, Path(PUBLIC_USI_DIR), dev_slug, inv_slug)
                        suggestions_count += len(new_suggestions)
                        logger.info(f"Added {len(new_suggestions)} suggestions to {inv1_id} ({dev_slug}/{inv_slug})")

    logger.info(f"Finished. Found {suggestions_count} new suggestions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect similar investments")
    parser.add_argument("--dev", type=str, help="Developer slug to scan within")
    parser.add_argument("--inv", type=str, help="Specific investment USI ID to scan for")
    parser.add_argument("--inv-slug", type=str, help="Specific investment slug to scan for (requires --dev)")
    args = parser.parse_args()
    
    detect_similar_invs(Path(USI_DATA_DIR), args.dev, args.inv, args.inv_slug)
