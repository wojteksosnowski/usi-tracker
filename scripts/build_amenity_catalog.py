"""Buduje python_worker/data/amenity_catalog.json (kanoniczne udogodnienia).

Punkty (`points`) pochodzą z HasłaMarketingowe.csv (kolumna HMUdogodnienia, wg USIfeature);
synonimy/grupy są utrzymywane ręcznie w CONCEPTS poniżej. Po uruchomieniu wypisuje pokrycie
(% wystąpień z kolumny `n` objętych katalogiem lub szumem).

    python scripts/build_amenity_catalog.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA = ROOT / "python_worker" / "data"
CSV_PATH = DATA / "HasłaMarketingowe.csv"
OUT_PATH = DATA / "amenity_catalog.json"

# (id, label, group, points, scored, aliases)
CONCEPTS = [
    # rekreacja / sport
    ("basen", "Basen", "rekreacja", 8, True, ["basen", "swimming_pool", "swimming pool", "pool"]),
    ("sauna", "Sauna", "rekreacja", 4, True, ["sauna"]),
    ("klub_fitness", "Klub fitness", "rekreacja", 4, True,
     ["klub fitness", "sala fitness", "strefa fitness", "fitness", "gym", "fitness_room"]),
    ("silownia", "Siłownia", "rekreacja", 4, True, ["siłownia", "silownia"]),
    ("sala_kinowa", "Sala kinowa", "rekreacja", 4, True, ["sala kinowa"]),
    ("sala_klubowa", "Sala klubowa", "rekreacja", 4, True, ["sala klubowa"]),
    ("sala_zabaw", "Sala zabaw", "rekreacja", 4, True, ["sala zabaw dla dzieci", "sala zabaw"]),
    ("coworking", "Strefa co-working", "usługi", 4, True,
     ["strefa co-workingu", "strafa co-workingu", "strefa coworkingu", "co-working", "coworking", "workroom"]),
    ("strefa_relaksu", "Strefa relaksu", "rekreacja", 4, True, ["strefa relaksu", "relax_area", "relax area"]),
    ("pomieszczenie_rekreacyjne", "Pomieszczenie rekreacyjne", "rekreacja", 2, True, ["pomieszczenie rekreacyjne"]),
    ("strefa_wypoczynku", "Strefa wypoczynku", "rekreacja", 0, True, ["strefa wypoczynku"]),
    ("plac_zabaw", "Plac zabaw", "teren", 0, True, ["plac zabaw", "plac zbaw", "teren: plac zabaw"]),
    ("silownia_plenerowa", "Siłownia plenerowa", "teren", 0, True, ["siłownia plenerowa"]),
    ("boisko", "Boisko", "teren", 0, True, ["boisko", "boiska sportowe", "boiska", "sport_fields"]),
    ("korty", "Korty tenisowe", "teren", 0, True, ["korty tenisowe", "kort tenisowy"]),
    ("teren_rekreacyjny", "Teren rekreacyjny", "teren", 0, True, ["teren rekreacyjny"]),
    ("patio", "Patio / dziedziniec", "teren", 0, True, ["patio / dziedziniec", "patio", "dziedziniec"]),
    ("akwen", "Własny akwen", "teren", 0, True, ["własny akwen"]),
    ("przystan", "Przystań dla łodzi", "teren", 0, True, ["przystań dla łodzi"]),
    ("ujecie_wody", "Własne ujęcie wody", "teren", 0, True, ["własne ujęcie wody"]),
    # usługi
    ("concierge", "Concierge", "usługi", 4, True, ["usługi concierge", "concierge"]),
    ("recepcja", "Recepcja", "usługi", 2, True, ["recepcja"]),
    ("lobby_recepcja", "Lobby z recepcją", "usługi", 4, True,
     ["eleganckie lobby wejściowe z recepcją", "lobby z recepcją", "lobby"]),
    ("pralnia", "Pralnia", "usługi", 1, True, ["pralnia"]),
    ("uslugi_w_budynku", "Usługi w budynku", "usługi", 0, True, ["usługi w budynku", "usługi", "lokale usługowe", "in_building"]),
    ("paczkomat", "Paczkomat", "usługi", 0, True, ["paczkomat"]),
    # bezpieczeństwo
    ("ochrona", "Ochrona", "bezpieczeństwo", 1, True, ["ochrona całodobowa", "ochrona", "monitoring / ochrona"]),
    ("monitoring", "Monitoring", "bezpieczeństwo", 1, True, ["monitoring", "cctv"]),
    ("system_alarmowy", "System alarmowy", "bezpieczeństwo", 0, True, ["system alarmowy"]),
    ("videodomofon", "Wideodomofon", "bezpieczeństwo", 0, True, ["videodomofon", "wideodomofon", "domofon", "wideofon", "wideodomofony", "videodomofony"]),
    ("teren_zamkniety", "Teren zamknięty", "bezpieczeństwo", 0, True,
     ["teren ogrodzony", "teren zamknięty", "osiedle zamknięte", "ogrodzone", "ogrodzony"]),
    ("czujnik_dymu", "Czujnik dymu", "bezpieczeństwo", 0, False, ["czujnik dymu"]),
    # budynek / technologia
    ("winda", "Winda", "budynek", 0, True, ["winda", "windy", "elevator", "elevators"]),
    ("niepelnosprawni", "Przystosowane dla niepełnosprawnych", "budynek", 0, True,
     ["przystosowane dla niepełnosprawnych", "przyjazny dla osób niepełnosprawnych", "dla niepełnosprawnych",
      "przystosowany dla niepełnosprawnych", "dostępny dla niepełnosprawnych", "disabled_friendly"]),
    ("rowerownia", "Rowerownia", "budynek", 1, True,
     ["rowerownia", "pomieszczenie na rowery", "wiata rowerowa", "przechowalnia rowerów", "stojaki rowerowe", "stojaki na rowery"]),
    ("wozkarnia", "Wózkarnia", "budynek", 1, True, ["wózkarnia", "wozkarnia"]),
    ("inteligentny_dom", "Inteligentny dom", "technologia", 0, True, ["inteligentny dom", "smart home"]),
    ("klimatyzacja", "Klimatyzacja", "technologia", 0, True, ["klimatyzacja", "air_conditioning"]),
    ("rekuperacja", "Rekuperacja", "technologia", 0, True, ["rekuperacja"]),
    ("pompa_ciepla", "Pompa ciepła", "technologia", 0, True, ["pompa ciepła"]),
    ("fotowoltaika", "Instalacja fotowoltaiczna", "technologia", 0, True, ["instalacja fotowoltaiczna", "fotowoltaika", "panele fotowoltaiczne"]),
    ("kotlownia", "Własna kotłownia", "technologia", 0, True, ["własna kotłownia"]),
    ("internet", "Internet", "technologia", 0, True, ["internet"]),
    ("tv_kablowa", "TV kablowa", "technologia", 0, True, ["tv kablowa", "telewizja kablowa"]),
    # parking
    ("parking_naziemny", "Parking naziemny", "parking", 0, True, ["parking naziemny", "miejsca parkingowe", "miejsce parkingowe"]),
    ("parking_podziemny", "Parking podziemny", "parking", 0, True,
     ["parking podziemny", "miejsce parkingowe podziemne", "garaż podziemny", "garaż", "hala garażowa", "garaż wielostanowiskowy"]),
    ("parking_goscie", "Miejsca parkingowe dla gości", "parking", 0, True, ["miejsca parkingowe dla gości"]),
    ("ladowarki_ev", "Ładowanie samochodów elektrycznych", "parking", 0, True,
     ["miejsce do ładowania samochodów elektrycznych", "ładowarki ev", "stacja ładowania"]),
    # zewnętrzne (cechy lokalu – nie punktowane)
    ("balkon", "Balkon", "zewnętrzne", 0, False, ["balkon", "balkony", "balcony"]),
    ("taras", "Taras", "zewnętrzne", 0, False, ["taras", "tarasy", "terrace"]),
    ("loggia", "Loggia", "zewnętrzne", 0, False, ["loggia"]),
    ("ogrodek", "Ogródek", "zewnętrzne", 0, False, ["ogródek", "ogródki", "garden"]),
    ("komorka", "Komórka lokatorska", "dodatkowe", 0, False,
     ["komórka lokatorska", "komórki lokatorskie", "powierzchnie dodatkowe: komórka lokatorska"]),
    ("piwnica", "Piwnica", "dodatkowe", 0, False, ["piwnica", "basement"]),
]

# Szum: nazwy kategorii TO i pola meta (regex dopasowywane do znormalizowanej etykiety).
NOISE = [
    r"^(teren|budynek|garaż|powierzchnie zewnętrzne|powierzchnie dodatkowe)$",
    r"^termin oddania\b.*",
    r"^dostępna liczba ofert\b.*",
    r"^wys(okość|\.)\s*(mieszkania|lokalu|apartamentu)\b.*",
    r"^\d[\d\s,\.]*\s*(m²|m2|m)?$",
]


def main():
    points_by_label = {}
    n_by_label = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                lbl = (row.get("HMLabel") or "").strip().lower()
                try:
                    n_by_label[lbl] = int(row.get("n") or 0)
                except ValueError:
                    n_by_label[lbl] = 0
                if row.get("HMUdogodnienia"):
                    try:
                        points_by_label[lbl] = int(row["HMUdogodnienia"])
                    except ValueError:
                        pass

    concepts = []
    seen_alias = {}
    for cid, label, group, points, scored, aliases in CONCEPTS:
        for a in aliases:
            if a in seen_alias:
                raise SystemExit(f"alias duplicate: {a!r} in {cid} and {seen_alias[a]}")
            seen_alias[a] = cid
        concepts.append({
            "id": cid, "label": label, "group": group,
            "points": points, "scored": scored, "aliases": aliases,
        })

    # sanity: punkty z CSV nie mogą być niższe niż w katalogu dla aliasu
    for a, cid in seen_alias.items():
        csv_pts = points_by_label.get(a)
        cat_pts = next(c["points"] for c in concepts if c["id"] == cid)
        if csv_pts is not None and csv_pts > cat_pts:
            print(f"UWAGA: {a!r} ma w CSV {csv_pts} pkt, a {cid} w katalogu {cat_pts}")

    OUT_PATH.write_text(
        json.dumps({"version": 1, "concepts": concepts, "noise": NOISE}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"zapisano {OUT_PATH} ({len(concepts)} pojęć)")

    from python_worker.services.amenity_normalizer import canonicalize, load_catalog
    load_catalog.cache_clear()
    total = covered = 0
    missing = []
    for lbl, n in n_by_label.items():
        if not n:
            continue
        total += n
        res = canonicalize([lbl])
        if res["canonical"] or res["noise"]:
            covered += n
        else:
            missing.append((n, lbl))
    if total:
        print(f"pokrycie: {covered}/{total} = {100 * covered / total:.1f}% wystąpień")
    for n, lbl in sorted(missing, reverse=True)[:25]:
        print(f"  nierozpoznane: {n:5d}  {lbl}")


if __name__ == "__main__":
    main()
