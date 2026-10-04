"""Parsowanie terminu oddania inwestycji i filtrowanie po zakresach."""
import re
from datetime import date

READY = 0  # porządek dla "gotowe do odbioru" (wcześniej niż jakikolwiek kwartał)

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}
_MONTH_Q = {"stycz": 1, "lut": 1, "marz": 1, "kwie": 2, "maj": 2, "czerw": 2,
            "lip": 3, "sierp": 3, "wrze": 3, "paźdz": 4, "listop": 4, "grud": 4}

_ISO_Q = re.compile(r"(\d{4})\s*-?\s*Q([1-4])", re.I)
_ROMAN_Q = re.compile(r"\b(IV|III|II|I)\s*kwarta[łl]\s*(\d{4})", re.I)
_MONTH_Y = re.compile(r"([a-zżźćńółęąś]+)\s+(\d{4})", re.I)
_YEAR = re.compile(r"\b(20\d{2})\b")


def _ord(year: int, quarter: int) -> int:
    return year * 4 + quarter


def current_quarter_ord(today: date | None = None) -> int:
    today = today or date.today()
    return _ord(today.year, (today.month - 1) // 3 + 1)


def parse_delivery(value) -> tuple[int, int] | None:
    """'2024-Q2 / 2024-Q3' -> (ord_min, ord_max); None gdy brak terminu."""
    if not value or not isinstance(value, str):
        return None
    text = value.replace("\xa0", " ")
    ords = []
    for y, q in _ISO_Q.findall(text):
        ords.append(_ord(int(y), int(q)))
    rest = _ISO_Q.sub(" ", text)
    for r, y in _ROMAN_Q.findall(rest):
        ords.append(_ord(int(y), _ROMAN[r.upper()]))
    rest = _ROMAN_Q.sub(" ", rest)
    for word, y in _MONTH_Y.findall(rest):
        for prefix, q in _MONTH_Q.items():
            if word.lower().startswith(prefix):
                ords.append(_ord(int(y), q))
                break
    if not ords:
        for y in _YEAR.findall(rest):
            ords.extend([_ord(int(y), 1), _ord(int(y), 4)])
    if re.search(r"gotow|odbi[oó]r|oddan|zako[nń]czon", text, re.I):
        ords.append(READY)
    if not ords:
        return None
    return min(ords), max(ords)


def delivery_years(value) -> list[int]:
    """Lata obejmowane terminem oddania; 'gotowe' i brak terminu pomijane."""
    rng = parse_delivery(value)
    if rng is None:
        return []
    lo, hi = rng
    if hi == READY:
        return []
    if lo == READY:  # 'gotowe' + konkretny kwartał: liczy się tylko kwartał
        lo = hi
    return list(range((lo - 1) // 4, (hi - 1) // 4 + 1))


def token_range(token: str, today: date | None = None) -> tuple[int, int] | None:
    """Token filtra -> zakres porządków. 'none' obsługiwany osobno.

    ready  - oddane (przed bieżącym kwartałem)
    2026   - cały rok;  2028+ - rok i później;  2026-Q3 - pojedynczy kwartał
    """
    token = token.strip()
    if token == "ready":
        return READY, current_quarter_ord(today) - 1
    m = re.fullmatch(r"(\d{4})-(\d{4})", token)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        if y1 > y2:
            raise ValueError(f"Odwrócony zakres lat: {token}")
        return _ord(y1, 1), _ord(y2, 4)
    m = re.fullmatch(r"(\d{4})-Q([1-4])", token, re.I)
    if m:
        o = _ord(int(m.group(1)), int(m.group(2)))
        return o, o
    m = re.fullmatch(r"(\d{4})(\+?)", token)
    if m:
        y = int(m.group(1))
        return _ord(y, 1), (10**9 if m.group(2) else _ord(y, 4))
    return None


def validate_tokens(tokens, today: date | None = None) -> None:
    """ValueError dla odwróconego zakresu lat."""
    for t in tokens:
        token_range(t, today)


def matches_delivery(value, tokens, today: date | None = None) -> bool:
    """Pusta lista tokenów = brak filtra."""
    if not tokens:
        return True
    rng = parse_delivery(value)
    if rng is None:
        return "none" in tokens
    for t in tokens:
        tr = token_range(t, today)
        if tr and rng[0] <= tr[1] and rng[1] >= tr[0]:
            return True
    return False
