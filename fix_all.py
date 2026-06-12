from pathlib import Path
import json

paths = [
  'Public/USIdata/unknown/zielony-brochow-7-indonezyjska-wroclaw-brochow-krzyki-mieszkania-na-sprzedaz/usi_to_9186660.json',
  'Public/USIdata/to-84163/kacpury-residence-antoniego-kacpury-warszawa-rembertow-nowy-rembertow-mieszkania-na-sprzedaz/usi_to_9232029.json',
  'Public/USIdata/to-33655/osiedle-contigo-siedzikowny-wroclaw-psie-pole-zawidawie-zakrzow-mieszkania-na-sprzedaz/usi_to_8942787.json',
  'Public/USIdata/to-3259/osiedle-witaj-etap-iii-bielicowa-poznan-naramowice-mieszkania-na-sprzedaz/usi_to_9231166.json',
  'Public/USIdata/to-112192/westo-wola-jana-kazimierza-72-warszawa-wola-odolany-mieszkania-na-sprzedaz/usi_to_9227388.json',
  'Public/USIdata/to-109184/rezydencja-swierkowa-etap-ii-radom-idalin-mieszkania-na-sprzedaz/usi_to_9209573.json'
]

for p in paths:
    fp = Path("/Volumes/Samsam/claude-py/usi-tracker") / p
    if fp.exists():
        data = json.loads(fp.read_text())
        uid = fp.name.replace("usi_", "").replace(".json", "")
        print(f"{uid} exists. Has usi_inv_id? {'usi_inv_id' in data}")
    else:
        print(f"{p} NOT FOUND")
