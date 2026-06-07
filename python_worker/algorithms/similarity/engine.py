import logging
from typing import List, Dict, Any, Set, Optional
from .strategies import (
    SimilarityStrategy,
    NameSimilarityStrategy,
    GeoProximityStrategy,
    SharedInvestmentStrategy,
    InvestmentTokenOverlapStrategy,
    normalize_name
)

logger = logging.getLogger(__name__)

class DeveloperMatcher:
    """Odpowiedzialny za proces parowania deweloperów na podstawie wstrzykniętych strategii."""
    
    def __init__(self, strategies: Optional[List[SimilarityStrategy]] = None) -> None:
        # Default zestaw pancernych strategii, jeśli klient nie wstrzyknie własnych
        self.strategies = strategies or [
            NameSimilarityStrategy(threshold=0.85),
            SharedInvestmentStrategy(),
            GeoProximityStrategy(),
            InvestmentTokenOverlapStrategy()
        ]

    def _is_excluded(self, d1: Dict[str, Any], d2: Dict[str, Any], dismissed_cache: Dict[str, Set[str]]) -> bool:
        """Sprawdza reguły wykluczające pary z parowania (baza danych / logika biznesowa)."""
        id1 = d1.get("usi_dev_id") or d1.get("id")
        id2 = d2.get("usi_dev_id") or d2.get("id")
        
        if not id1 or not id2:
            return True

        # 1. Tożsamość obiektów
        if str(id1) == str(id2):
            return True

        # 2. Sprawdzenie cache odrzuconych w UI
        s_id1, s_id2 = str(id1), str(id2)
        if s_id2 in dismissed_cache.get(s_id1, set()) or s_id1 in dismissed_cache.get(s_id2, set()):
            return True
            
        # 3. Istniejące relacje architektoniczne (Master/Parent)
        m1, m2 = d1.get("master_id"), d2.get("master_id")
        if m1 and m1 == m2:
            return True
            
        # Parent ID model
        if d1.get("parent_id") == id2 or d2.get("parent_id") == id1:
            return True
            
        return False

    def find_suggestions_for_developer(
        self, 
        target_dev: Dict[str, Any], 
        all_developers: List[Dict[str, Any]], 
        dismissed_cache: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje propozycje powiązań dla jednego konkretnego dewelopera.
        """
        suggestions: List[Dict[str, Any]] = []
        target_id = target_dev.get("usi_dev_id") or target_dev.get("id")
        
        if not target_id:
            return []

        for candidate in all_developers:
            if self._is_excluded(target_dev, candidate, dismissed_cache):
                continue
                
            best_score = 0.0
            best_reason: Optional[str] = None
            
            # Ewaluacja potoku strategii
            for strategy in self.strategies:
                try:
                    score, reason = strategy.calculate(target_dev, candidate)
                    if score > best_score:
                        best_score = score
                        best_reason = reason
                except Exception as strategy_error:
                    logger.error(
                        f"Krytyczny błąd strategii {strategy.__class__.__name__} "
                        f"dla par {target_id} <> {candidate.get('usi_dev_id') or candidate.get('id')}: {strategy_error}",
                        exc_info=True
                    )
                    
            if best_score > 0.0 and best_reason:
                suggestions.append({
                    "source_id": target_id,
                    "target_id": candidate.get("usi_dev_id") or candidate.get("id"),
                    "target_slug": candidate.get("developer_slug") or candidate.get("slug") or "unknown",
                    "reason": best_reason,
                    "score": round(best_score, 4)
                })
                
        # Sortowanie od najwyższego prawdopodobieństwa trafienia
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions

def calculate_similarities(devs: List[Dict[str, Any]], dismissed_cache: Dict[str, Set[str]] = None) -> List[Dict[str, Any]]:
    """
    Główny punkt wejścia algorytmu podobieństwa (legacy wrapper).
    Porównuje każdego dewelopera z każdym (N^2), biorąc pod uwagę odrzucone pary.
    """
    matcher = DeveloperMatcher()
    all_suggestions = []
    
    dismissed_cache = dismissed_cache or {}
    
    logger.info(f"Rozpoczynam analizę podobieństwa dla {len(devs)} deweloperów...")
    
    # Optymalizacja: tylko deweloperzy z ID (wymóg ID-only)
    valid_devs = [d for d in devs if d.get("usi_dev_id")]
    
    for i, dev1 in enumerate(valid_devs):
        # find_suggestions_for_developer jest O(N), wywołane w pętli daje O(N^2)
        # ale używamy podzbioru (i+1:) aby uniknąć duplikatów i(A,B) vs i(B,A)
        # Jednak find_suggestions_for_developer przeszukuje CAŁĄ listę.
        # Dla zachowania kompatybilności z dotychczasowym calculate_similarities, 
        # które zwracało listę par, użyjemy matcher.find_suggestions_for_developer na okrojonej liście
        # lub zostawimy prostszą pętlę tutaj dla wydajności N(N-1)/2.
        
        dev1_id = dev1.get("usi_dev_id")
        remaining_devs = valid_devs[i+1:]
        
        suggestions = matcher.find_suggestions_for_developer(dev1, remaining_devs, dismissed_cache)
        all_suggestions.extend(suggestions)
                
        if (i + 1) % 100 == 0:
            logger.info(f"Przetworzono {i + 1}/{len(valid_devs)} deweloperów...")

    return all_suggestions
