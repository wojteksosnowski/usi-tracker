import pytest
from python_worker.algorithms.similarity.strategies import (
    NameSimilarityStrategy, 
    InvestmentTokenOverlapStrategy,
    SharedInvestmentStrategy,
    GeoProximityStrategy
)

def test_regression_dev_28975_and_28976_name_match():
    """Weryfikacja czy łączniki nie blokują wykrywania formy prawnej sp z o.o."""
    dev1 = {"usi_dev_id": "DEV-28975", "name": "022-investments", "developer_slug": "022-investments"}
    dev2 = {"usi_dev_id": "DEV-28976", "name": "022-investments-sp-z-o-o", "developer_slug": "022-investments-sp-z-o-o"}
    
    strategy = NameSimilarityStrategy()
    score, reason = strategy.calculate(dev1, dev2)
    
    assert score == 1.0
    assert "'022'" in reason


def test_regression_dev_26257_and_28951_token_overlap():
    """Weryfikacja czy podział etapów inwestycji (Zabrze/Grzybowice) paruje deweloperów."""
    dev1 = {
        "usi_dev_id": "DEV-26257", 
        "name": "4estetica Sp. z o.o.",
        "developer_slug": "4estetica-sp-z-oo",
        "investments": [{"slug": "4estetica-sp-z-oo/osiedle-hallera-grzybowice"}]
    }
    dev2 = {
        "usi_dev_id": "DEV-28951", 
        "name": "4estetica",
        "developer_slug": "4estetica",
        "investments": [{"slug": "4estetica/osiedle-hallera-zabrze"}]
    }
    
    # Test dopasowania nazwowego
    name_strategy = NameSimilarityStrategy()
    n_score, _ = name_strategy.calculate(dev1, dev2)
    assert n_score == 1.0
    
    # Test dopasowania po tokenach projektów
    token_strategy = InvestmentTokenOverlapStrategy()
    t_score, reason = token_strategy.calculate(dev1, dev2)
    
    assert t_score >= 0.70
    assert "hallera" in reason

def test_regression_geo_proximity():
    """Weryfikacja dopasowania geolokalizacyjnego w promieniu < 100m."""
    dev1 = {
        "usi_dev_id": "DEV-1",
        "investments": [{"coords": [52.2319, 21.0067]}] # Warszawa, Centrum
    }
    dev2 = {
        "usi_dev_id": "DEV-2",
        "investments": [{"coords": [52.2320, 21.0068]}] # Bardzo blisko
    }
    
    from python_worker.algorithms.similarity.strategies import GeoProximityStrategy
    strategy = GeoProximityStrategy()
    score, reason = strategy.calculate(dev1, dev2)
    
    assert score >= 0.85
    assert "bliskość geolokalizacyjna" in reason

def test_regression_unique_prefix():
    """Weryfikacja dopasowania po unikalnym prefiksie (Indicator 4)."""
    dev1 = {"usi_dev_id": "DEV-3", "name": "Xentarix Development"}
    dev2 = {"usi_dev_id": "DEV-4", "name": "Xentarix Group"}
    
    strategy = NameSimilarityStrategy()
    score, reason = strategy.calculate(dev1, dev2)
    
    assert score >= 0.80
    assert "xentarix" in reason.lower()

def test_regression_dev_26394_and_26395_budlex():
    """Weryfikacja pary Budlex (DEV-26394) i Budlex Sp. z o.o. (DEV-26395)."""
    dev1 = {
        "usi_dev_id": "DEV-26394", 
        "name": "Budlex", 
        "developer_slug": "budlex",
        "investments": [
            {"slug": "budlex/enklawa"},
            {"slug": "budlex/urzecze"}
        ]
    }
    dev2 = {
        "usi_dev_id": "DEV-26395", 
        "name": "Budlex Sp. z o.o.", 
        "developer_slug": "budlex-sp-z-oo",
        "investments": [
            {"slug": "budlex-sp-z-oo/osiedle-enklawa-bydgoszcz"},
            {"slug": "budlex-sp-z-oo/urzecze-bydgoszcz"}
        ]
    }
    
    # Test 1: Nazwa (1.0 score)
    name_strategy = NameSimilarityStrategy()
    n_score, n_reason = name_strategy.calculate(dev1, dev2)
    assert n_score == 1.0
    assert "budlex" in n_reason.lower()
    
    # Test 2: Tokeny inwestycji (zbieżność po końcówkach i słowach unikalnych)
    token_strategy = InvestmentTokenOverlapStrategy()
    t_score, t_reason = token_strategy.calculate(dev1, dev2)
    assert t_score >= 0.70
    assert "enklawa" in t_reason.lower() or "urzecze" in t_reason.lower()

def test_regression_dev_26020_and_26021_3msbud():
    """Weryfikacja pary 3msbud-sp-z-o-o (DEV-26020) i 3msbud-sp-z-oo (DEV-26021)."""
    dev1 = {"usi_dev_id": "DEV-26020", "name": "3msbud sp. z o.o.", "developer_slug": "3msbud-sp-z-o-o"}
    dev2 = {"usi_dev_id": "DEV-26021", "name": "3msbud sp z oo", "developer_slug": "3msbud-sp-z-oo"}
    
    strategy = NameSimilarityStrategy()
    score, reason = strategy.calculate(dev1, dev2)
    
    assert score == 1.0
    assert "3msbud" in reason.lower()

def test_regression_dev_26045_and_26046_acciona():
    """Weryfikacja pary acciona-nieruchomosci (DEV-26045) i acciona-nieruchomosci-sp-z-oo (DEV-26046)."""
    dev1 = {"usi_dev_id": "DEV-26045", "name": "Acciona Nieruchomości", "developer_slug": "acciona-nieruchomosci"}
    dev2 = {"usi_dev_id": "DEV-26046", "name": "Acciona Nieruchomości Sp. z o.o.", "developer_slug": "acciona-nieruchomosci-sp-z-oo"}
    
    # Test 1: Nazwa (1.0 score po usunięciu 'nieruchomości' i 'sp z oo')
    name_strategy = NameSimilarityStrategy()
    n_score, n_reason = name_strategy.calculate(dev1, dev2)
    assert n_score == 1.0
    assert "acciona" in n_reason.lower()
    
    # Test 2: Inwestycje (zbieżność zbozowa, kamienna-28)
    dev1["investments"] = [{"slug": "acciona-nieruchomosci/zbozowa"}]
    dev2["investments"] = [{"slug": "acciona-nieruchomosci-sp-z-oo/zbozowa-gdynia-cisowa"}]
    
    token_strategy = InvestmentTokenOverlapStrategy()
    t_score, t_reason = token_strategy.calculate(dev1, dev2)
    assert t_score >= 0.70
    assert "zbozowa" in t_reason.lower()

# --- NEGATIVE CASES (Should NOT match) ---

def test_negative_bjm_and_apm():
    """Weryfikacja czy BJM i APM nie są parowane mimo wspólnego członu 'Development'."""
    dev1 = {"usi_dev_id": "DEV-26341", "name": "BJM Development Sp. z o.o. Sp.k."}
    dev2 = {"usi_dev_id": "DEV-26178", "name": "APM Development"}
    
    # Test Name similarity
    strategy = NameSimilarityStrategy()
    score, _ = strategy.calculate(dev1, dev2)
    assert score < 0.50 # "bjm" vs "apm"
    
    # Test Token overlap (no shared tokens)
    dev1["investments"] = [{"slug": "bjm/pasaz-abrahama"}]
    dev2["investments"] = [{"slug": "apm/nowy-marysin"}]
    
    token_strategy = InvestmentTokenOverlapStrategy()
    t_score, _ = token_strategy.calculate(dev1, dev2)
    assert t_score == 0.0

def test_negative_generic_names():
    """Weryfikacja czy generyczne nazwy branżowe nie dają fałszywych trafień."""
    # "Dom" i "Dom Invest" - słowo "Dom" (jeśli nie jest odfiltrowane) mogłoby dać 100% inkluzji.
    # Upewnijmy się, że róg "Dom" jest bezpieczny lub ignorowany.
    dev1 = {"usi_dev_id": "DEV-X", "name": "Dom"}
    dev2 = {"usi_dev_id": "DEV-Y", "name": "Dom Invest"}
    
    strategy = NameSimilarityStrategy()
    score, _ = strategy.calculate(dev1, dev2)
    
    # Jeśli "dom" nie jest w ignored_tokens, n1="dom", n2="dom". Wynik 1.0 (złe!)
    # Warto dodać "dom" do ignored_tokens jeśli występuje jako samodzielny token branżowy.
    # Ale deweloper "Dom Development" ma rdzeń "dom". 
    # To jest trudny przypadek - "Dom" vs "Dom Development" to prawdopodobnie ten sam deweloper.
    # Ale "Dom" vs "Inne Domy" już nie.
    assert score < 0.85 or score == 0.0 # Oczekujemy braku dopasowania jeśli to tylko szum.

def test_dom_development_match():
    """Weryfikacja czy 'Dom Development' jest parowany przez inwestycje mimo ignorowania nazwy."""
    dev1 = {
        "usi_dev_id": "DEV-D1", 
        "name": "Dom Development",
        "investments": [{"slug": "dom-dev/osiedle-leśne"}]
    }
    dev2 = {
        "usi_dev_id": "DEV-D2", 
        "name": "Dom Development S.A.",
        "investments": [{"slug": "dom-dev-sa/osiedle-leśne"}]
    }
    
    # Name strategy fails (0.0)
    name_strategy = NameSimilarityStrategy()
    n_score, _ = name_strategy.calculate(dev1, dev2)
    assert n_score == 0.0
    
    # Shared investment strategy MUST catch it
    token_strategy = SharedInvestmentStrategy()
    s_score, reason = token_strategy.calculate(dev1, dev2)
    
    assert s_score >= 0.75
    assert "osiedle-leśne" in reason
