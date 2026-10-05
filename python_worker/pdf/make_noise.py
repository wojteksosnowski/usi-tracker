"""Generuje assets/noise.png — kafelkowalne, drobne ziarno (film/druk) do nakładki na gradienty USI.

Uruchom: venv/bin/python python_worker/pdf/make_noise.py
Kafel 1536 px wyświetlany jako 130 mm (≈300 dpi). Dwie oktawy szumu gaussowskiego (drobna + lekko rozmyta)
dają miękkie ziarno zamiast pikselowego „śniegu"; kafelkowanie bez szwów (rozmycie na planszy 3×3).
Szum nie jest ziarnowany seedem — PNG jest commitowany, nie generuje się w runtime.
Wynik: biały szum w kanale alfa (LA) o niskim kryciu (brandbook: 8–14%).
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

SIZE = 1536
MAX_ALPHA = 26  # ≈10% krycia przy najjaśniejszych ziarnach
OUT = Path(__file__).resolve().parent / "assets" / "noise.png"


def _octave(sigma, blur):
    """Gaussowski szum SIZE×SIZE (średnia 128), rozmyty z zawijaniem krawędzi."""
    tile = Image.effect_noise((SIZE, SIZE), sigma)
    big = Image.new("L", (SIZE * 3, SIZE * 3))
    for ix in range(3):
        for iy in range(3):
            big.paste(tile, (ix * SIZE, iy * SIZE))
    if blur:
        big = big.filter(ImageFilter.GaussianBlur(blur))
    return big.crop((SIZE, SIZE, SIZE * 2, SIZE * 2))


def main():
    fine = _octave(60, 0.6)
    soft = _octave(60, 1.6)
    grain = ImageChops.add(fine, soft, scale=2)  # średnia z dwóch oktaw
    # kontrast: rozciągnij wokół 128, potem alfa = odchylenie od średniej (ziarno jaśniejsze → bardziej kryje)
    lum = grain.point(lambda v: max(0, min(255, int((v - 128) * 2.4 + 128))))
    alpha = lum.point(lambda v: min(MAX_ALPHA, abs(v - 128) * MAX_ALPHA // 64))
    white = Image.new("L", lum.size, 255)
    dark = Image.new("L", lum.size, 0)
    # jasne ziarna → białe, ciemne → czarne (overlay-podobny efekt bez blend modes)
    color = Image.composite(white, dark, lum.point(lambda v: 255 if v >= 128 else 0))
    Image.merge("LA", (color, alpha)).save(OUT, optimize=True)
    print(f"zapisano {OUT} ({OUT.stat().st_size} B)")


if __name__ == "__main__":
    main()
