from .merger import Merger
from usi_scrapers.adapters.rp import RPAdapter
from usi_scrapers.adapters.otodom import OtodomAdapter
from usi_scrapers.adapters.to import TOAdapter

class AdapterFactory:
    _adapters = {
        "rp": RPAdapter,
        "otodom": OtodomAdapter,
        "oto": OtodomAdapter,
        "tabelaofert": TOAdapter,
        "to": TOAdapter
    }

    @classmethod
    def get_adapter(cls, portal_name):
        portal_name = portal_name.lower()
        adapter_cls = cls._adapters.get(portal_name)
        if not adapter_cls:
            raise ValueError(f"No adapter registered for portal: {portal_name}")
        return adapter_cls

__all__ = ["AdapterFactory", "Merger", "RPAdapter", "OtodomAdapter", "TOAdapter"]
