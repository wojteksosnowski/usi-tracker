import pytest
from python_worker.algorithms.similarity.engine import DeveloperMatcher, calculate_similarities

def test_engine_pipeline_selects_best_score():
    """Weryfikacja czy silnik poprawnie procesuje potok i wybiera najwyższy score z dostępnych strategii."""
    # Deweloperzy mają skrajnie różne nazwy (NameSimilarity = 0.0), ale identyczną inwestycję
    dev1 = {
        "usi_dev_id": "DEV-1001",
        "developer_slug": "alpha-builders",
        "name": "Alpha Builders",
        "investments": [{"slug": "alpha-builders/osiedle-leśne"}]
    }
    dev2 = {
        "usi_dev_id": "DEV-1002",
        "developer_slug": "omega-development",
        "name": "Omega Development",
        "investments": [{"slug": "omega-development/osiedle-leśne"}]
    }
    
    matcher = DeveloperMatcher()
    suggestions = matcher.find_suggestions_for_developer(dev1, [dev2], dismissed_cache={})
    
    assert len(suggestions) == 1
    assert suggestions[0]["source_id"] == "DEV-1001"
    assert suggestions[0]["target_id"] == "DEV-1002"
    # SharedInvestmentStrategy powinno dać wysoki score (>= 0.75) mimo braku zgodności nazwowej
    assert suggestions[0]["score"] >= 0.75
    assert "Współdzielenie tych samych inwestycji" in suggestions[0]["reason"]


def test_engine_respects_exclusion_rules():
    """Weryfikacja czy silnik odrzuca deweloperów o tym samym master_id lub odrzuconych w cache UI."""
    dev1 = {
        "usi_dev_id": "DEV-28975",
        "developer_slug": "022-investments",
        "name": "022-investments",
        "master_id": "DM-0877"
    }
    dev2 = {
        "usi_dev_id": "DEV-28976",
        "developer_slug": "022-investments-sp-z-o-o",
        "name": "022-investments sp z o.o.",
        "master_id": "DM-0877" # Wspólny master_id - powinni zostać wykluczeni
    }
    
    matcher = DeveloperMatcher()
    suggestions = matcher.find_suggestions_for_developer(dev1, [dev2], dismissed_cache={})
    assert len(suggestions) == 0, "Silnik nie wykluczył deweloperów o tym samym master_id"

    # Test wykluczenia przez dismissed_cache
    dev2_no_master = dev2.copy()
    dev2_no_master.pop("master_id")
    dev1_no_master = dev1.copy()
    dev1_no_master.pop("master_id")
    
    dismissed = {"DEV-28975": {"DEV-28976"}}
    suggestions_dismissed = matcher.find_suggestions_for_developer(dev1_no_master, [dev2_no_master], dismissed_cache=dismissed)
    assert len(suggestions_dismissed) == 0, "Silnik zignorował cache odrzuconych par z UI"


def test_regression_real_coordinates_format_handling():
    """REGRESJA: Weryfikacja czy format współrzędnych z plików json (lista w 'coordinates') nie powoduje crasha AttributeError."""
    dev1 = {
        "usi_dev_id": "DEV-28976",
        "investments": [{
            "slug": "022-investments/szalasa-3",
            "coordinates": [52.320269, 20.974111] # Rzeczywisty format tablicy z bazy danych
        }]
    }
    dev2 = {
        "usi_dev_id": "DEV-28975",
        "investments": [{
            "slug": "022-investments/szalasa-5",
            "coordinates": [52.320255, 20.974453]
        }]
    }
    
    matcher = DeveloperMatcher()
    # Jeśli metoda _get_coords odpali .get() na liście, test natychmiast scrashuje, ujawniając błąd produkcyjny
    try:
        suggestions = matcher.find_suggestions_for_developer(dev1, [dev2], dismissed_cache={})
    except AttributeError as e:
        pytest.fail(f"Krytyczny błąd struktur danych silnika: {e}. Lista potraktowana jako słownik.")
        
    assert len(suggestions) == 1
    assert suggestions[0]["score"] >= 0.90
    assert "bliskość geolokalizacyjna" in suggestions[0]["reason"]


def test_regression_batch_versus_single_scan_asymmetry():
    """REGRESJA: Weryfikacja czy pełne skanowanie (calculate_similarities) generuje spójne powiązania dwukierunkowe."""
    dev1 = {
        "usi_dev_id": "DEV-28975",
        "developer_slug": "022-investments",
        "name": "022-investments"
    }
    dev2 = {
        "usi_dev_id": "DEV-28976",
        "developer_slug": "022-investments-sp-z-o-o",
        "name": "022-investments sp z o.o."
    }
    
    # Pełna baza danych przekazana do analizy par
    pool = [dev1, dev2]
    all_suggestions = calculate_similarities(pool, dismissed_cache={})
    
    # Aby UI nie gubiło sugestii, relacja musi zostać wykryta niezależnie od kierunku
    has_dev1_to_dev2 = any(s["source_id"] == "DEV-28975" and s["target_id"] == "DEV-28976" for s in all_suggestions)
    has_dev2_to_dev1 = any(s["source_id"] == "DEV-28976" and s["target_id"] == "DEV-28975" for s in all_suggestions)
    
    assert has_dev1_to_dev2, "Brak relacji DEV-28975 -> DEV-28976"
    assert has_dev2_to_dev1, "Brak relacji DEV-28976 -> DEV-28975 (asymetria parowania w batchu)"


def test_diagnostic_dump_tool():
    """Weryfikacja działania narzędzia diagnostycznego dump_sequence_matcher_analysis."""
    from python_worker.algorithms.similarity.strategies import dump_sequence_matcher_analysis
    
    dev1 = {"usi_dev_id": "DEV-D1", "name": "Atal Spółka Akcyjna"}
    dev2 = {"usi_dev_id": "DEV-D2", "name": "Atal SA"}
    
    # Wywołanie nie powinno rzucić błędem i wypisać dane na stderr
    dump_sequence_matcher_analysis(dev1, dev2)
