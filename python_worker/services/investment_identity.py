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

    def build_index(self):
        """Triggers a full rebuild of the investment index."""
        from python_worker.investment_index import rebuild
        return rebuild(self.data_dir, self.public_usi_dir)

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

    def get_investment_resources_by_slug(self, dev_slug: str, inv_slug: str) -> dict | None:
        """
        @deprecated: Always use get_investment_resources(usi_inv_id).
        Legacy fallback method to resolve resources by slug.
        """
        from python_worker.investment_index import load as load_index
        index = load_index(self.data_dir)
        entry = next((e for e in index if e.get("developer_slug") == dev_slug and e.get("investment_slug") == inv_slug), None)
        
        if not entry:
            return None

        return self.get_investment_resources(entry["usi_inv_id"])

    def _map_resources_from_entry(self, entry: dict) -> dict | None:
        """Determines physical file locations strictly via TechnicalDataManager."""
        portal = entry.get("portal")
        portal_id = entry.get("portal_id")
        
        if not portal or not portal_id:
            sources = entry.get("sources") or {}
            for p in ("rp", "oto", "to"):
                if p in sources and sources[p].get("id"):
                    portal = p
                    portal_id = sources[p].get("id")
                    break

        from python_worker.config import get_scraper_config
        from usi_scrapers.manager import TechnicalDataManager
        import logging
        
        config = get_scraper_config()
        if not config or not portal or not portal_id:
            return None

        tech_manager = TechnicalDataManager(config)
        inv_dir = tech_manager.get_investment_path(portal, str(portal_id))
        images_dir = tech_manager.get_image_path(portal, str(portal_id))
        
        if not inv_dir:
            return None

        anchor_file = inv_dir / f"usi_{portal}_{portal_id}.json"
        raw_file = inv_dir / f"raw_{portal}_{portal_id}.json"
        
        # Meta/ratings files are still partially slug-based in names, but located in ID-resolved folder
        inv_slug = entry.get("investment_slug")
        meta_file = inv_dir / f"meta_{inv_slug}_ratings.json" if inv_slug else None

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
            "images_dir": images_dir if images_dir and images_dir.exists() else None,
            "metadata": {
                "portal": portal,
                "portal_id": portal_id,
                "slug": f"{entry.get('developer_slug')}/{inv_slug}"
            }
        }

