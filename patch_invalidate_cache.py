import re

file_path = "python_worker/services/investment_service.py"
with open(file_path, "r") as f:
    content = f.read()

patch = """    def invalidate_cache(self, inv_id: str = None):
        \"\"\"Invalidates cache entries and syncs to index.\"\"\"
        if inv_id:
            self._cache.pop(inv_id, None)
            from python_worker.api.utils import _load_investment
            from python_worker.investment_index import get_investment_index
            entry = _load_investment(system_id=inv_id, fast_index=True)
            if entry:
                entry.pop("image_urls", None)
                entry.pop("nearby_investments", None)
                get_investment_index().add_or_update(inv_id, entry)
        else:
            self._cache.clear()
            from python_worker.investment_index import get_investment_index
            get_investment_index().rebuild()"""

content = re.sub(
    r"    def invalidate_cache\(self, inv_id: str = None\):\n.*?self\._cache\.clear\(\)",
    patch,
    content,
    flags=re.DOTALL
)

with open(file_path, "w") as f:
    f.write(content)

print("Patch applied to investment_service.py!")
