import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-tracker")
from python_worker.api.blueprints.investments import investment_service
import logging

logging.basicConfig(level=logging.DEBUG)

invs = [
    {
        "id": "4BuBt",
        "url": "https://www.otodom.pl/pl/inwestycja/miasto-polskich-mistrzow-olimpijskich-ii-ID4BuBt",
        "slug": "miasto-polskich-mistrzow-olimpijskich-ii-ID4BuBt",
        "dev_name": "Profbud"
    }
]

res = investment_service.process_batch("oto", invs)
print(f"Saved: {res}")
