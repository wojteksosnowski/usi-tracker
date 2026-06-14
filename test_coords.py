import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from python_worker.investment_index import get_investment_index

idx = get_investment_index()
idx.load_or_rebuild()

inv = idx.get_entry_by_id("INV-30056")
if not inv:
    print("Not found")
else:
    print(inv.get("coords"))
    
