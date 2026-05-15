import re
import unicodedata

_SLUG_REPLACE = str.maketrans("łŁ", "lL")

def slugify(text: str) -> str:
    # Polish ł/Ł must be transliterated before NFKD (NFKD doesn't decompose them)
    text = text.translate(_SLUG_REPLACE)
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")
