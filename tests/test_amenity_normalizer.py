import pytest

from python_worker.services.amenity_normalizer import (
    build_amenities, canonicalize, load_catalog, split_label,
)
from python_worker.services.amenity_scorer import compute_amenity_score, suggest_udogodnienia


def test_catalog_loaded():
    assert load_catalog()["concepts"], "katalog udogodnień jest pusty (zła ścieżka?)"


@pytest.mark.parametrize("labels", [
    ["Winda: tak"], ["windy"], ["Windy"], ["winda"], ["elevators"],
])
def test_elevator_synonyms_across_portals(labels):
    assert canonicalize(labels)["canonical"] == ["winda"]


def test_cross_portal_union_dedups():
    res = canonicalize(["Winda: tak", "windy", "Windy", "teren ogrodzony", "Teren zamknięty"])
    assert res["canonical"] == ["teren_zamkniety", "winda"]


def test_dimensions_and_decimal_commas_not_split():
    assert split_label("taras (12,27 m²), ogródek (20,46 m²)") == ["taras", "ogródek"]
    assert canonicalize(["balkon (3,10\xa0m²)"])["canonical"] == ["balkon"]


def test_category_prefix_split():
    res = canonicalize(["Garaż: hala garażowa, parking naziemny"])
    assert res["canonical"] == ["parking_naziemny", "parking_podziemny"]


@pytest.mark.parametrize("label", [
    "Teren", "Budynek", "Powierzchnie zewnętrzne", "Termin oddania: A - III kwartał 2027",
    "Dostępna liczba ofert: 61", "Wysokość mieszkania: 2,60 - 2,80 m", "34",
])
def test_noise(label):
    res = canonicalize([label])
    assert not res["canonical"] and not res["unmatched"] and res["noise"]


def test_negative_value_skipped():
    assert canonicalize(["Monitoring: nie"]) == {"canonical": [], "unmatched": [], "noise": []}


def test_unmatched_kept_not_scored():
    res = canonicalize(["xyz dziwne", "XYZ dziwne"])
    assert res["unmatched"] == ["xyz dziwne"]
    assert compute_amenity_score(["xyz dziwne"])["score"] == 0


def test_build_amenities_idempotent():
    first = build_amenities(["basen", "Windy", "foo"], ["1"])
    second = build_amenities(first["labels"], first["raw_codes"], extra_canonical=first["canonical"])
    assert first == second
    assert first["labels"] == ["Basen", "Winda", "foo"]


def test_score_counts_each_concept_once():
    score = compute_amenity_score(["basen", "Basen", "swimming_pool", "sauna"])
    assert score["score"] == 12
    assert {m["code"] for m in score["matched"]} == {"basen", "sauna"}
    assert suggest_udogodnienia(score["score"]) == 3


def test_union_score_from_canonical_not_max():
    a = canonicalize(["basen"])["canonical"]
    b = canonicalize(["sauna"])["canonical"]
    assert compute_amenity_score([], canonical=sorted(set(a) | set(b)))["score"] == 12
