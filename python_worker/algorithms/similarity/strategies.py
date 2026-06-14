import re
import math
import sys
from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from typing import Dict, Any, Optional, Tuple, Set

class SimilarityStrategy(ABC):
    """Abstrakcyjna klasa bazowa dla reguł oceny podobieństwa deweloperów."""
    
    @abstractmethod
    def calculate(self, dev1: Dict[str, Any], dev2: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        """
        Zwraca krotkę: (ocena_podobieństwa [0.0 - 1.0], uzasadnienie_wyboru).
        """
        pass

class NameSimilarityStrategy(SimilarityStrategy):
    """Zoptymalizowana tekstowa ocena podobieństwa nazw odporna na anomalie interpunkcyjne."""
    
    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold
        self.ignored_tokens: Set[str] = {
            "spółka", "z", "oo", "ooo", "sa", "s_a", "spk", "sc", "sj", "spj", 
            "holding", "group", "development", "investment", "investments", 
            "invest", "nieruchomości", "domy", "mieszkania", "bud", "sp", "spv", "o",
            "akcyjna", "komandytowa", "jawna", "cywilna", "zoo", "dom"
        }

    def _ultra_clean(self, name: Optional[str]) -> str:
        if not name:
            return ""
        # Zamiana łączników, kropek i przecinków na spacje przed podziałem na tokeny
        t = name.lower().replace("-", " ").replace(".", " ").replace(",", " ")
        tokens = t.split()
        # Odfiltrowanie śmieciowych tokenów prawnych i branżowych
        cleaned_tokens = [tok for tok in tokens if tok not in self.ignored_tokens]
        return "".join(cleaned_tokens)

    def calculate(self, dev1: Dict[str, Any], dev2: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        # Prefer names, fall back to slugs
        n1 = self._ultra_clean(dev1.get("name") or dev1.get("developer_slug"))
        n2 = self._ultra_clean(dev2.get("name") or dev2.get("developer_slug"))
        
        if not n1 or not n2:
            return 0.0, None
            
        matcher = SequenceMatcher(None, n1, n2)
        ratio = matcher.ratio()

        # Wymuszenie dumpu dla konkretnej, problematycznej pary deweloperów
        # if "022" in n1 or "022" in n2:
        #     dump_sequence_matcher_analysis(dev1, dev2, self)

        if ratio >= self.threshold:
            return ratio, f"Wysokie podobieństwo nazw rdzeniowych: '{n1}' ({int(ratio * 100)}%)"
        
        # Fallback for inclusion (Indicator 4)
        if len(n1) > 3 and len(n2) > 3:
            if n1 in n2 or n2 in n1:
                return 0.80, f"Rdzeń '{n1}' zawiera się w '{n2}' (lub odwrotnie)"
                
        return 0.0, None

class InvestmentTokenOverlapStrategy(SimilarityStrategy):
    """Analizuje rzadkie słowa wspólne w nazwach inwestycji (Indicator 2)."""
    
    def __init__(self, min_token_len: int = 4) -> None:
        self.min_token_len = min_token_len
        self.common_words: Set[str] = {"osiedle", "park", "apartamenty", "mieszkania", "ogrody", "villa", "nowe", "nowa"}

    def _extract_unique_tokens(self, dev: Dict[str, Any]) -> Set[str]:
        tokens: Set[str] = set()
        for inv in dev.get("investments", []):
            slug = inv.get("slug")
            if not slug:
                continue
            # Rozbicie sluga na słowa (inv-slug part)
            inv_part = slug.split("/")[-1]
            words = inv_part.lower().split("-")
            for w in words:
                if len(w) >= self.min_token_len and w not in self.common_words:
                    tokens.add(w)
        return tokens

    def calculate(self, dev1: Dict[str, Any], dev2: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        tokens1 = self._extract_unique_tokens(dev1)
        tokens2 = self._extract_unique_tokens(dev2)
        
        intersect = tokens1.intersection(tokens2)
        if len(intersect) >= 1: # Minimum jedno unikalne słowo wspólne (np. 'hallera')
            score = min(0.90, 0.60 + (len(intersect) * 0.10))
            return score, f"Zbieżność unikalnych nazw inwestycji: {', '.join(intersect)}"
            
        return 0.0, None

class GeoProximityStrategy(SimilarityStrategy):
    """Ocenia czy deweloperzy budują w promieniu < 100m (Indicator 3)."""
    
    def __init__(self, max_dist_m: float = 100.0) -> None:
        self.max_dist_m = max_dist_m

    def _haversine_m(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6_371_000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _get_coords(self, inv: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        coords = inv.get("coordinates")
        if not coords:
            # Fallback dla starego klucza "coords"
            coords = inv.get("coords")
            
        if isinstance(coords, list) and len(coords) >= 2:
            try:
                return float(coords[0]), float(coords[1])
            except (ValueError, TypeError):
                return None
        elif isinstance(coords, dict):
            lat = coords.get("lat")
            lng = coords.get("lng")
            if lat is not None and lng is not None:
                try:
                    return float(lat), float(lng)
                except (ValueError, TypeError):
                    pass
        return None

    def calculate(self, dev1: Dict[str, Any], dev2: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        invs1 = [self._get_coords(i) for i in dev1.get("investments", []) if self._get_coords(i)]
        invs2 = [self._get_coords(i) for i in dev2.get("investments", []) if self._get_coords(i)]
        
        if not invs1 or not invs2:
            return 0.0, None

        for c1 in invs1:
            for c2 in invs2:
                dist = self._haversine_m(c1[0], c1[1], c2[0], c2[1])
                if dist <= self.max_dist_m:
                    return 0.90, f"Ekstremalna bliskość geolokalizacyjna inwestycji ({dist:.1f} m)"
        
        return 0.0, None

class SharedInvestmentStrategy(SimilarityStrategy):
    """Wyszukuje deweloperów współdzielących identyczne inwestycje."""
    
    def calculate(self, dev1: Dict[str, Any], dev2: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        slugs1 = {i.get("slug", "").split("/")[-1] for i in dev1.get("investments", []) if i.get("slug")}
        slugs2 = {i.get("slug", "").split("/")[-1] for i in dev2.get("investments", []) if i.get("slug")}
        
        common_slugs = {s for s in slugs1 if s and s in slugs2}
        if common_slugs:
            count = len(common_slugs)
            score = min(0.99, 0.75 + (count * 0.05))
            return score, f"Współdzielenie tych samych inwestycji po końcówkach slugów ({count} szt.: {', '.join(list(common_slugs)[:3])})"
            
        return 0.0, None

def dump_sequence_matcher_analysis(dev1: Dict[str, Any], dev2: Dict[str, Any], strategy: Any = None) -> None:
    """
    Wykonuje pełny zrzut diagnostyczny operacji porównywania ciągów tekstowych.
    Wypisuje transformację tokenów oraz dokładne bloki dopasowań i opkody SequenceMatcher.
    """
    strat = strategy or NameSimilarityStrategy()
    
    raw_n1 = dev1.get("name") or dev1.get("developer_slug") or ""
    raw_n2 = dev2.get("name") or dev2.get("developer_slug") or ""
    
    # Przechwycenie stanu po ultra-czyszczeniu
    clean_n1 = strat._ultra_clean(raw_n1)
    clean_n2 = strat._ultra_clean(raw_n2)
    
    matcher = SequenceMatcher(None, clean_n1, clean_n2)
    ratio = matcher.ratio()
    
    print("=" * 80, file=sys.stderr)
    print(f"DIAGNOSTYKA SEQUENCE MATCHER: {dev1.get('usi_dev_id')} <=> {dev2.get('usi_dev_id')}", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"REKORD 1: [Raw]: '{raw_n1}' -> [Cleaned]: '{clean_n1}'", file=sys.stderr)
    print(f"REKORD 2: [Raw]: '{raw_n2}' -> [Cleaned]: '{clean_n2}'", file=sys.stderr)
    print(f"WYNIK (Ratio): {ratio:.4f} (Threshold: {getattr(strat, 'threshold', 'N/A')})", file=sys.stderr)
    print("-" * 80, file=sys.stderr)
    
    # 1. Zrzut identycznych bloków (Matching Blocks)
    print("BLOKI DOPASOWANE (Matching Blocks):", file=sys.stderr)
    matching_blocks = matcher.get_matching_blocks()
    for block in matching_blocks:
        if block.size > 0:
            fragment = clean_n1[block.a : block.a + block.size]
            print(f"  - Pozycja w R1: {block.a}, Pozycja w R2: {block.b}, Długość: {block.size} -> Tekst: '{fragment}'", file=sys.stderr)
            
    print("-" * 80, file=sys.stderr)
    
    # 2. Zrzut instrukcji transformacji (Opcodes)
    print("OPERACJE TRANSFORMAJI (Opcodes):", file=sys.stderr)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        str1_chunk = clean_n1[i1:i2]
        str2_chunk = clean_n2[j1:j2]
        print(f"  - Akcja: {tag:<10} | R1[{i1}:{i2}] ('{str1_chunk}') -> R2[{j1}:{j2}] ('{str2_chunk}')", file=sys.stderr)
        
    print("=" * 80, file=sys.stderr)


def normalize_name(name: Optional[str]) -> str:
    """Helper for backward compatibility."""
    return NameSimilarityStrategy()._ultra_clean(name)
