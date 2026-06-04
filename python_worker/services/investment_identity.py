import json
from pathlib import Path

class InvestmentIdentityResolver:
    """
    Universal ID-to-File mapping for investments.
    Returns a map of all physical files associated with a USI Investment ID.
    
    ARCHITECTURAL MANDATE: ID-ONLY PRIORITY.
    This is the primary method for resolving physical resources. Never use slugs
    for file lookup if an ID is available.
    """
    def __init__(self, data_dir: Path | str, public_usi_dir: Path | str):
        self.data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
        self.public_usi_dir = Path(public_usi_dir) if isinstance(public_usi_dir, str) else public_usi_dir

    def get_investment_resources(self, inv_id: str) -> dict | None:
        from python_worker.investment_index import load as load_index
        index = load_index(self.data_dir)
        if not index:
            # Fallback to scan if index missing
            for p in self.data_dir.rglob("usi_*.json"):
                if "usi_dev_" in p.name: continue
                try:
                    data = json.loads(p.read_text())
                    if data.get("usi_inv_id") == inv_id:
                        entry = {
                            "usi_inv_id": inv_id,
                            "developer_slug": p.parent.parent.name,
                            "investment_slug": p.parent.name,
                            "portal": data.get("portal"),
                            "portal_id": data.get("portal_id"),
                            "sources": data.get("sources")
                        }
                        return self._map_resources_from_entry(entry)
                except: continue
            return None

        # Fast path via index
        entry = next((e for e in index if e.get("usi_inv_id") == inv_id), None)
        if not entry:
            return None

        return self._map_resources_from_entry(entry)

    def get_investment_resources_by_slug(self, dev_slug: str, inv_slug: str) -> dict:
        """Fallback method to resolve resources by slug when ID is not yet available."""
        entry = {
            "usi_inv_id": f"temp_{inv_slug}",
            "developer_slug": dev_slug,
            "investment_slug": inv_slug,
            "portal": None,
            "portal_id": None,
            "sources": {}
        }
        return self._map_resources_from_entry(entry)

    def _map_resources_from_entry(self, entry: dict) -> dict:
        dev_slug = entry["developer_slug"]
        inv_slug = entry["investment_slug"]
        inv_dir = self.data_dir / dev_slug / inv_slug
        
        portal = entry.get("portal")
        portal_id = entry.get("portal_id")
        
        if not portal or not portal_id:
            sources = entry.get("sources", {})
            for p in ("rp", "oto", "to"):
                if p in sources and sources[p].get("id"):
                    portal = p
                    portal_id = sources[p].get("id")
                    break
        
        # Determine anchor file precisely
        anchor_file = None
        if portal and portal_id:
            f = inv_dir / f"usi_{portal}_{portal_id}.json"
            if f.exists():
                anchor_file = f
        
        if not anchor_file:
            # Fallback for legacy slug-based anchors
            for p in (inv_dir / f"usi_{inv_slug}.json", 
                      inv_dir / f"usi_rp_{inv_slug}.json", 
                      inv_dir / f"usi_oto_{inv_slug}.json", 
                      inv_dir / f"usi_to_{inv_slug}.json"):
                if p.exists():
                    anchor_file = p
                    break

        # Determine raw file
        raw_file = None
        if portal and portal_id:
            f = inv_dir / f"raw_{portal}_{portal_id}.json"
            if f.exists():
                raw_file = f
        
        if not raw_file and portal:
            # Try slug-based raw file
            f = inv_dir / f"raw_{portal}_{inv_slug}.json"
            if f.exists():
                raw_file = f
        
        if not raw_file:
            # Last resort: find any raw file for this portal
            matches = sorted(list(inv_dir.glob(f"raw_{portal}_*.json"))) if portal else []
            if matches:
                raw_file = matches[-1]

        # Determine meta/ratings file
        meta_file = inv_dir / f"meta_{inv_slug}_ratings.json"
        if not meta_file.exists():
            # Fallback for legacy meta files
            for p in (inv_dir / f"meta_rp_{inv_slug}.json", 
                      inv_dir / f"meta_oto_{inv_slug}.json", 
                      inv_dir / f"meta_to_{inv_slug}.json"):
                if p.exists():
                    meta_file = p
                    break
        
        # Images dir
        images_dir = self.public_usi_dir / dev_slug / inv_slug
        if not images_dir.exists():
            # Check if it was pinned to a different dev folder
            if anchor_file:
                try:
                    data = json.loads(anchor_file.read_text())
                    img_list = data.get("ratings", {}).get("imgList") or ""
                    if "/Public/USI/" in img_list:
                        import re
                        m = re.search(r'/Public/USI/([^/]+)/', img_list)
                        if m:
                            images_dir = self.public_usi_dir / m.group(1) / inv_slug
                except: pass

        return {
            "id": entry["usi_inv_id"],
            "type": "investment",
            "base_dir": inv_dir,
            "files": {
                "anchor": anchor_file if anchor_file and anchor_file.exists() else None,
                "raw": raw_file if raw_file and raw_file.exists() else None,
                "meta": meta_file if meta_file and meta_file.exists() else None,
                "logs": [inv_dir / "deletion_list.json"] if (inv_dir / "deletion_list.json").exists() else []
            },
            "images_dir": images_dir if images_dir.exists() else None,
            "metadata": {
                "portal": portal,
                "portal_id": portal_id,
                "slug": f"{dev_slug}/{inv_slug}"
            }
        }
