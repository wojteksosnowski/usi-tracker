import re
from usi_scrapers import resolve_path

class JsonPathExtractor:
    """
    Deprecated. Use usi_scrapers.resolve_path instead.
    This class is kept for backward compatibility during migration.
    """

    @staticmethod
    def _unwrap_rp(val):
        """Legacy helper for RP unwrapping. resolve_path handles this internally now."""
        if isinstance(val, dict) and "value" in val and "type" in val:
            return val["value"]
        return val

    @classmethod
    def get_value(cls, data, path_cfg, default=None):
        val = resolve_path(data, path_cfg)
        return val if val is not None else default
