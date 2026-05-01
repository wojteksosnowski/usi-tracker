import re
import json
import logging
from .fetcher import fetch_html
from .image_saver import save_images
from .csv_importer import slugify

logger = logging.getLogger(__name__)


def fetch_to_html(url: str) -> str:
    """Fetch tabelaofert page HTML using the centralized Fetcher."""
    return fetch_html(url) or ""


def parse_to_product(html: str) -> dict:
    """Extract schema.org Product JSON-LD from page HTML. Returns {} if not found."""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    for s in scripts:
        if '"@type":"Product"' in s or '"@type": "Product"' in s:
            try:
                # Some scripts might have junk before/after JSON
                content = s.strip()
                if content.startswith("self.__next_f.push"):
                    # This is a Next.js RSC fragment, handled separately in extract_gallery_urls
                    continue
                d = json.loads(content)
                if isinstance(d, list):
                    for item in d:
                        if item.get("@type") == "Product": return item
                elif d.get("@type") == "Product":
                    return d
            except json.JSONDecodeError:
                continue
    return {}


def extract_geo(product: dict) -> tuple:
    """Return (lat, lng) from first individual offer. All offers share the same coords."""
    offers_data = product.get("offers", {})
    if not isinstance(offers_data, dict): return None, None
    
    offers = offers_data.get("offers", [])
    if not isinstance(offers, list): return None, None
    
    for offer in offers:
        geo = offer.get("itemOffered", {}).get("geo", {})
        lat = geo.get("latitude")
        lng = geo.get("longitude")
        if lat is not None and lng is not None:
            try:
                return float(lat), float(lng)
            except (TypeError, ValueError):
                continue
    return None, None


def extract_additional_prop(product: dict, name: str) -> str | None:
    """Return value from schema.org additionalProperty list by name."""
    props = product.get("additionalProperty", [])
    if not isinstance(props, list): return None
    
    for prop in props:
        if prop.get("name") == name:
            return prop.get("value")
    return None


def extract_gallery_urls(html: str) -> list[str]:
    """Extract gallery image URLs from RSC fragments (galeria.zdjecia section)."""
    found_urls = []
    
    # 1. Look for RSC fragments
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    for s in scripts:
        if '"galeria"' in s and '"zdjecia"' in s:
            # URLs are JSON-encoded within the RSC push string: \"url\":\"https://...\"
            urls = re.findall(
                r'\\"url\\":\\"(https?://content\\.tabelaofert\\.pl/[^\\]+)',
                s,
            )
            if urls:
                found_urls.extend([u.rstrip('"') for u in urls])
                
    # 2. Fallback: all unique content.tabelaofert.pl image URLs found in page
    # Also handle protocol-relative //content.tabelaofert.pl
    regex = r'(?:https?:)?//content\.tabelaofert\.pl/[^\s\"\\<>]+\.(?:webp|jpg|jpeg|png)'
    found = re.findall(regex, html, re.IGNORECASE)
    for u in found:
        if u.startswith("//"):
            found_urls.append("https:" + u)
        else:
            found_urls.append(u)
            
    return list(dict.fromkeys(found_urls))


def _cdn_filename(url: str) -> str:
    """Strip CDN transform prefix and return bare filename, also stripping hash suffixes."""
    # Pattern: .../anything,ID-filename.ext
    fname = url.rsplit("/", 1)[-1]
    m = re.search(r"[^/]+-/(.+)$", url)
    if m: fname = m.group(1)
    else:
        # Try another common pattern on TO: /quality_...,scale_...,filename.ext
        parts = fname.split(",")
        if len(parts) > 1: fname = parts[-1]

    # Strip cache-buster/hash suffix like _e94b5737.webp or _a789f3d8.webp
    fname = re.sub(r'_[a-f0-9]{8}\.', '.', fname)
    return fname


def _investment_image_prefix(image_url: str) -> str | None:
    """Derive investment-specific filename prefix from product['image'] URL."""
    fname = _cdn_filename(image_url)
    stem = fname.rsplit(".", 1)[0]
    
    # Remove things like -1, -2 at the end before date check
    stem = re.sub(r'-\d+$', '', stem)
    
    m = re.search(r"-\d{8}", stem)
    if m:
        return stem[: m.start()]
    
    # If no date, take first 3-4 segments as prefix
    parts = stem.split("-")
    if len(parts) > 3:
        return "-".join(parts[:4])
    return "-".join(parts)


def filter_investment_images(urls: list[str], product: dict) -> list[str]:
    """Filter CDN image URLs to only gallery photos for this investment.

    Filters by investment-specific filename prefix, excludes maps/logos,
    and deduplicates by filename after stripping hashes.
    """
    main_image = product.get("image")
    if isinstance(main_image, list) and main_image:
        main_image = main_image[0]
        
    prefix = _investment_image_prefix(str(main_image)) if main_image else None
    logger.info(f"Filtering images with prefix: {prefix}")

    candidates = []
    for url in urls:
        fname = _cdn_filename(url)
        # Exclude maps, logos, icons
        if any(fname.startswith(p) for p in ["mapa-", "logo-", "icon-", "avatar-"]):
            continue
            
        if prefix and not fname.startswith(prefix):
            prefix_parts = prefix.split("-")
            short_prefix = "-".join(prefix_parts[:3]) if len(prefix_parts) > 2 else prefix
            if not fname.startswith(short_prefix):
                continue
        
        candidates.append(url)

    if not candidates and urls:
        logger.warning("Strict filtering returned 0 images. Relaxing filter.")
        for url in urls:
            fname = _cdn_filename(url)
            if not any(fname.startswith(p) for p in ["mapa-", "logo-", "icon-", "avatar-"]):
                candidates.append(url)

    by_filename: dict[str, tuple[int, str]] = {}
    for url in candidates:
        fname = _cdn_filename(url)
        # Find scale_N to pick best resolution
        m = re.search(r"scale_(\d+)", url)
        scale = int(m.group(1)) if m else 0
        if fname not in by_filename or scale > by_filename[fname][0]:
            by_filename[fname] = (scale, url)
            
    return [v[1] for v in by_filename.values()]


def _extract_to_id(url: str) -> str | None:
    m = re.search(r",i(\d+)(?:[/?]|$)", url)
    return m.group(1) if m else None


def discover_to_investments(dev_slug_or_id: str) -> list[dict]:
    """
    Discovers investments for a given developer slug or ID on TabelaOfert.pl.
    """
    if not dev_slug_or_id:
        return []
        
    url = f"https://tabelaofert.pl/katalog-firm/deweloperzy/{dev_slug_or_id}"
    logger.info(f"Discovering TabelaOfert investments for: {dev_slug_or_id}")
    
    html = fetch_to_html(url)
    if not html: return []
    
    links = re.findall(r'href="(/inwestycja/[^"]+,i\d+)"', html)
    seen_urls = set()
    offers = []
    for l in links:
        full_url = f"https://tabelaofert.pl{l}"
        if full_url not in seen_urls:
            seen_urls.add(full_url)
            slug_part = l.split("/")[-1].split(",")[0]
            name = slug_part.replace("-", " ").title()
            offers.append({
                "url": full_url,
                "name": name,
                "slug": slug_part
            })
            
    return offers

def scrape_tabelaofert(url: str, dev_slug: str, inv_slug: str) -> dict:
    """Scrape a tabelaofert.pl investment page and return normalized result dict."""
    logger.info(f"Scraping TabelaOfert: {url}")
    html = fetch_to_html(url)
    if not html:
        return {"error": "Could not fetch HTML"}

    product = parse_to_product(html)
    if not product:
        logger.warning(f"No schema.org Product found for {url}")
        # Try to find images anyway if we have HTML
        gallery_urls = extract_gallery_urls(html)
        if gallery_urls:
            logger.info(f"Found {len(gallery_urls)} images via fallback despite no Product schema")
            saved = save_images(gallery_urls, dev_slug, inv_slug)
            return {"error": "Missing Product schema", "images_count": len(saved)}
        return {"error": "Could not find schema.org Product in page"}

    # Developer name
    brand_name = product.get("brand", {}).get("name", "")
    
    # Resolve developer slug if it's generic
    if dev_slug in ("unknown", "tabelaofert") and brand_name:
        resolved_dev_slug = slugify(brand_name)
        if resolved_dev_slug:
            logger.info(f"Resolved developer slug from TabelaOfert brand: {resolved_dev_slug}")
            dev_slug = resolved_dev_slug

    lat, lng = extract_geo(product)
    product["url"] = url

    # Address
    offers_data = product.get("offers", {})
    offers = offers_data.get("offers", []) if isinstance(offers_data, dict) else []
    
    address_obj = {}
    if offers and isinstance(offers[0], dict):
        address_obj = offers[0].get("itemOffered", {}).get("address", {})
        
    street = address_obj.get("streetAddress")
    city = address_obj.get("addressLocality")
    region = address_obj.get("addressRegion")

    # Fallback for address from description if structured data is missing
    if (not street or not city) and product.get("description"):
        desc = product.get("description", "")
        # Look for parts separated by ✔️ or ➤
        parts_segments = re.split(r"[✔️➤]", desc)
        for segment in parts_segments:
            segment = segment.strip()
            # An address segment usually contains 'ul.' or starts with city name and has commas
            if "ul." in segment or (city and city in segment):
                parts = [p.strip() for p in segment.split(",")]
                if len(parts) >= 2:
                    city = parts[0]
                    street = parts[-1]
                    if len(parts) > 2:
                        region = ", ".join(parts[1:-1])
                    break
    
    address = ", ".join(filter(None, [street, city])) or None

    # Price range
    try:
        price_min = float(offers_data.get("lowPrice") or 0) or None
        price_max = float(offers_data.get("highPrice") or 0) or None
    except (TypeError, ValueError):
        price_min = price_max = None

    # Images
    gallery_urls = extract_gallery_urls(html)
    filtered_urls = filter_investment_images(gallery_urls, product)
    
    logger.info(f"Found {len(gallery_urls)} raw URLs, {len(filtered_urls)} filtered for {inv_slug}")
    
    saved = save_images(filtered_urls, dev_slug, inv_slug)
    image_paths = [f"/Public/USI/{dev_slug}/{inv_slug}/{fname}" for fname in saved]

    # Amenities
    amenities = []
    props = product.get("additionalProperty", [])
    if isinstance(props, list):
        _meta = {"Wysokość mieszkania", "Termin oddania", "Dostępna liczba ofert"}
        amenities = [
            {"name": p["name"], "value": p["value"]}
            for p in props if isinstance(p, dict) and p.get("name") not in _meta
        ]

    # Clean Name extraction from HTML
    # TabelaOfert structure: <h1 class="..."><span class="...">ATAL Aura</span><span class="...">ATAL S.A. - mieszkania na sprzedaż</span></h1>
    # We want the first span inside h1.
    clean_name = product.get("name")
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if h1_match:
        h1_content = h1_match.group(1)
        # Find first span
        span_match = re.search(r"<span[^>]*>(.*?)</span>", h1_content, re.DOTALL)
        if span_match:
            clean_name = span_match.group(1).strip()
            # Remove any residual HTML tags
            clean_name = re.sub(r"<[^>]+>", "", clean_name)
    
    # Fallback cleaning if HTML extraction failed or returned too much
    if clean_name:
        # Remove " - mieszkania na sprzedaż" and similar suffixes
        clean_name = re.sub(r"\s+-\s+mieszkania.*$", "", clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r"\s+-\s+lokale.*$", "", clean_name, flags=re.IGNORECASE)

    # Inject clean name back into product for the adapter to use
    product["name"] = clean_name
    product["images_count"] = len(saved)
    product["image_paths"] = image_paths
    # Inject extracted location data for the adapter as fallback
    product["_extracted_location"] = {
        "address": address,
        "city": city,
        "region": region,
        "latitude": lat,
        "longitude": lng
    }

    return {
        "source": "tabelaofert.pl",
        "to_id": _extract_to_id(url),
        "to_url": url,
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "usi_folder_path": f"/Public/USI/{dev_slug}/{inv_slug}/",
        "name": clean_name or product.get("name"),
        "developer_name": brand_name or None,
        "address": address,
        "city": city,
        "region": region,
        "latitude": lat,
        "longitude": lng,
        "price_min": price_min,
        "price_max": price_max,
        "properties_count": offers_data.get("offerCount"),
        "construction_date_upper": extract_additional_prop(product, "Termin oddania"),
        "amenities": amenities,
        "images_count": len(saved),
        "image_paths": image_paths,
        "raw_details": product,
    }
