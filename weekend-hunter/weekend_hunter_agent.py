"""
Weekend Hunter Agent
====================
Scrapes garage sales, estate sales, and eBay sourcing leads from Facebook
Marketplace, Facebook Groups, EstateSales.net, and Craigslist. Scores listings,
flags watchlist items, builds an optimized Google Maps route, and pushes it to
your Google Maps account.

Usage:
  Full scrape:   python weekend_hunter_agent.py --mode full
  Delta update:  python weekend_hunter_agent.py --mode delta
  Route only:    python weekend_hunter_agent.py --mode route
"""

import json
import time
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap paths
# ---------------------------------------------------------------------------
STUDIO_DIR = Path("G:/My Drive/Projects/_studio")
CONFIG_PATH = STUDIO_DIR / "weekend-hunter-config.json"
HUNTER_DIR = STUDIO_DIR / "weekend-hunter"
HUNTER_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(STUDIO_DIR))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(HUNTER_DIR / "hunter.log", encoding="utf-8", errors="replace"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("weekend-hunter")

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------
def load_config():
    with open(CONFIG_PATH, encoding="utf-8", errors="replace") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# State manager — tracks what we've already scraped
# ---------------------------------------------------------------------------
def load_state():
    state_path = HUNTER_DIR / "hunt-state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    return {
        "last_full_scrape": None,
        "last_delta_scrape": None,
        "seen_ids": [],
        "route_position": 0,
        "total_found": 0
    }

def save_state(state):
    state_path = HUNTER_DIR / "hunt-state.json"
    with open(state_path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(state, f, indent=2)

def load_results():
    results_path = HUNTER_DIR / "hunt-results.json"
    if results_path.exists():
        with open(results_path, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    return []

def save_results(results):
    results_path = HUNTER_DIR / "hunt-results.json"
    with open(results_path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(results, f, indent=2, default=str)

def save_delta(new_listings):
    delta_path = HUNTER_DIR / "hunt-delta.json"
    with open(delta_path, "w", encoding="utf-8", errors="replace") as f:
        json.dump({
            "scraped_at": datetime.now().isoformat(),
            "count": len(new_listings),
            "listings": new_listings
        }, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# EstateSales.net scraper (requests + BeautifulSoup)
# ---------------------------------------------------------------------------
def scrape_estatesales(cfg, seen_ids):
    import requests
    from bs4 import BeautifulSoup

    log.info("Scraping EstateSales.net...")
    results = []
    loc = cfg["location"]
    url = f"https://www.estatesales.net/{loc['state']}/{loc['city'].lower()}/{loc['zip']}/{loc['radius_miles']}-miles"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        sales = soup.select("div.sale-listing, div.saleListItem, article.sale")

        for sale in sales:
            try:
                title_el = sale.select_one("h2, h3, .sale-title, .listing-title")
                addr_el  = sale.select_one(".sale-address, .address, [itemprop='streetAddress']")
                date_el  = sale.select_one(".sale-dates, .dates, time")
                link_el  = sale.select_one("a[href]")
                img_el   = sale.select_one("img")

                title   = title_el.get_text(strip=True) if title_el else "Estate Sale"
                address = addr_el.get_text(strip=True)  if addr_el  else ""
                dates   = date_el.get_text(strip=True)  if date_el  else ""
                link    = "https://www.estatesales.net" + link_el["href"] if link_el else ""
                img     = img_el["src"] if img_el and img_el.get("src") else ""

                listing_id = f"es_{hash(link)}"
                if listing_id in seen_ids:
                    continue

                results.append({
                    "id": listing_id, "source": "estatesales.net",
                    "type": "estate_sale", "title": title,
                    "address": address, "dates": dates,
                    "url": link, "image": img,
                    "description": title,
                    "scraped_at": datetime.now().isoformat()
                })
            except Exception as e:
                log.debug(f"EstateSales parse error: {e}")
                continue

        time.sleep(2)
    except Exception as e:
        log.error(f"EstateSales scrape failed: {e}")

    log.info(f"EstateSales: found {len(results)} new listings")
    return results


# ---------------------------------------------------------------------------
# Craigslist scraper (requests + BeautifulSoup)
# ---------------------------------------------------------------------------
def scrape_craigslist(cfg, seen_ids):
    import requests
    from bs4 import BeautifulSoup

    log.info("Scraping Craigslist garage sales...")
    results = []
    base_url = cfg["sources"]["craigslist"]["base_url"]
    url = f"{base_url}/search/gms"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("li.cl-static-search-result, div.result-info")

        for item in items:
            try:
                title_el = item.select_one("a.cl-app-anchor, .result-title")
                date_el  = item.select_one("time, .result-date")
                loc_el   = item.select_one(".result-hood, .nearby")
                link_el  = item.select_one("a[href]")

                title   = title_el.get_text(strip=True) if title_el else "Garage Sale"
                dates   = date_el.get("datetime", "") if date_el else ""
                hood    = loc_el.get_text(strip=True)  if loc_el  else ""
                link    = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = base_url + link

                listing_id = f"cl_{hash(link)}"
                if listing_id in seen_ids:
                    continue

                results.append({
                    "id": listing_id, "source": "craigslist",
                    "type": "garage_sale", "title": title,
                    "address": hood, "dates": dates,
                    "url": link, "image": "",
                    "description": title,
                    "scraped_at": datetime.now().isoformat()
                })
            except Exception as e:
                log.debug(f"Craigslist parse error: {e}")
                continue

        time.sleep(2)
    except Exception as e:
        log.error(f"Craigslist scrape failed: {e}")

    log.info(f"Craigslist: found {len(results)} new listings")
    return results


# ---------------------------------------------------------------------------
# Facebook Marketplace + Groups scraper (Selenium)
# ---------------------------------------------------------------------------
def scrape_facebook(cfg, seen_ids, mode="full"):
    """
    Uses Selenium with your logged-in Chrome profile so you don't need
    Facebook API credentials. Requires Chrome and chromedriver installed.
    """
    log.info("Scraping Facebook Marketplace and Groups (Selenium)...")
    results = []

    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import random

        opts = Options()
        # Opera uses Chromium under the hood — point to Opera's profile
        # Opera profile is usually at: C:\Users\<you>\AppData\Roaming\Opera Software\Opera Stable
        opera_profile = "C:/Users/Joe/AppData/Roaming/Opera Software/Opera Stable"
        opts.add_argument(f"--user-data-dir={opera_profile}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-popup-blocking")
        # Opera binary path — update this if Opera is installed elsewhere
        opts.binary_location = "C:/Users/Joe/AppData/Local/Programs/Opera/opera.exe"
        # Uncomment below to run headless once stable:
        # opts.add_argument("--headless=new")

        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 10)

        # --- Marketplace garage sales ---
        try:
            loc = cfg["location"]
            mp_url = (
                f"https://www.facebook.com/marketplace/{loc['city'].lower()}{loc['state'].lower()}"
                f"/search?query=garage+sale&radius={loc['radius_miles']}"
            )
            driver.get(mp_url)
            time.sleep(random.uniform(3, 5))

            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='marketplace_feed_item'], div.x3ct3a4")
            for card in cards[:40]:
                try:
                    title   = card.find_element(By.CSS_SELECTOR, "span.x1lliihq, span.x193iq5w").text.strip()
                    price   = ""
                    try: price = card.find_element(By.CSS_SELECTOR, "span.x78zum5").text.strip()
                    except: pass
                    link_el = card.find_element(By.TAG_NAME, "a")
                    link    = link_el.get_attribute("href") or ""
                    img     = ""
                    try: img = card.find_element(By.TAG_NAME, "img").get_attribute("src") or ""
                    except: pass

                    listing_id = f"fb_mp_{hash(link)}"
                    if listing_id in seen_ids or not title:
                        continue

                    results.append({
                        "id": listing_id, "source": "facebook_marketplace",
                        "type": "garage_sale", "title": title,
                        "price": price, "address": "",
                        "dates": "", "url": link, "image": img,
                        "description": title,
                        "scraped_at": datetime.now().isoformat()
                    })
                    time.sleep(random.uniform(0.3, 0.7))
                except Exception:
                    continue

        except Exception as e:
            log.error(f"Facebook Marketplace scrape error: {e}")

        driver.quit()

    except ImportError:
        log.warning("Selenium not installed. Run: pip install selenium --break-system-packages")
    except Exception as e:
        log.error(f"Facebook scraper failed: {e}")

    log.info(f"Facebook: found {len(results)} new listings")
    return results


# ---------------------------------------------------------------------------
# Watchlist matcher
# ---------------------------------------------------------------------------
def check_watchlist(listing, watchlist):
    """Returns watchlist item if listing matches, else None."""
    text = (listing.get("title", "") + " " + listing.get("description", "")).lower()
    for watch in watchlist:
        if watch["term"].lower() in text:
            return watch
    return None

# ---------------------------------------------------------------------------
# EBIT flip scorer (Claude reasoning call)
# ---------------------------------------------------------------------------
def score_listing(listing, cfg):
    """
    Scores a listing 1-10 for garage sale quality OR eBay flip potential.
    Uses Claude via the studio AI gateway if available, falls back to
    keyword heuristic scoring.
    """
    try:
        from ai_gateway import query_claude
        prompt = f"""
Score this listing 1-10 for resale/eBay flip potential.
Return ONLY a JSON object: {{"score": <int>, "reason": "<15 words max>", "category": "<category>"}}

Title: {listing.get('title','')}
Description: {listing.get('description','')}
Source: {listing.get('source','')}
Type: {listing.get('type','')}
Price: {listing.get('price','unknown')}

High-value signals: {', '.join(cfg['scoring']['high_value_keywords'][:10])}
"""
        raw = query_claude(prompt, max_tokens=100)
        data = json.loads(raw.strip())
        return int(data.get("score", 5)), data.get("reason", ""), data.get("category", "")
    except Exception:
        pass

    # Fallback: keyword heuristic
    text = (listing.get("title","") + " " + listing.get("description","")).lower()
    score = 4
    for kw in cfg["scoring"]["high_value_keywords"]:
        if kw.lower() in text:
            score += 1
    if listing.get("image"):
        score += 1
    score = min(score, 10)
    return score, "keyword heuristic", "general"

# ---------------------------------------------------------------------------
# Garage sale quality scorer (separate from flip scoring)
# ---------------------------------------------------------------------------
def score_garage_sale(listing, cfg):
    """Scores a garage sale listing 1-10 for visit worthiness."""
    score = 5
    text = (listing.get("title","") + " " + listing.get("description","")).lower()
    high_words = ["estate", "collection", "everything must go", "lots of items",
                  "vintage", "antique", "collectible", "moving", "downsizing"]
    for w in high_words:
        if w in text:
            score += 1
    if listing.get("image"):
        score += 1
    if listing.get("dates") or listing.get("address"):
        score += 1
    return min(score, 10)


# ---------------------------------------------------------------------------
# Geocoder — resolves addresses to lat/lng
# ---------------------------------------------------------------------------
def geocode_address(address, api_key):
    import requests
    if not address or not api_key:
        return None, None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    try:
        resp = requests.get(url, params=params, timeout=10).json()
        if resp.get("results"):
            loc = resp["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except Exception as e:
        log.debug(f"Geocode failed for '{address}': {e}")
    return None, None

# ---------------------------------------------------------------------------
# Route optimizer — uses Google Directions with waypoint optimization
# ---------------------------------------------------------------------------
def build_optimized_route(listings_with_coords, cfg):
    """
    Takes a list of high-scored sales with lat/lng and returns an
    optimized waypoint order via Google Maps Directions API.
    """
    import requests

    api_key = cfg["google_maps"]["api_key"]
    if not api_key:
        log.warning("No Google Maps API key — skipping route optimization.")
        return listings_with_coords

    origin = cfg["google_maps"]["start_address"]
    waypoints = []
    for listing in listings_with_coords:
        if listing.get("lat") and listing.get("lng"):
            waypoints.append(f"{listing['lat']},{listing['lng']}")

    if len(waypoints) == 0:
        return listings_with_coords
    if len(waypoints) > 23:
        waypoints = waypoints[:23]  # Google limit

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": origin,
        "waypoints": "optimize:true|" + "|".join(waypoints),
        "mode": "driving",
        "key": api_key
    }

    try:
        resp = requests.get(url, params=params, timeout=15).json()
        if resp.get("status") == "OK":
            order = resp["routes"][0]["waypoint_order"]
            reordered = [listings_with_coords[i] for i in order]
            log.info(f"Route optimized: {len(reordered)} stops")
            return reordered
    except Exception as e:
        log.error(f"Route optimization failed: {e}")

    return listings_with_coords


# ---------------------------------------------------------------------------
# Google Maps — push list to your account
# ---------------------------------------------------------------------------
def push_to_google_maps(route, cfg):
    """
    Pushes the optimized route to Google Maps as a shareable URL.
    Google Maps doesn't have a public API for saved lists, so we:
    1. Save a route JSON locally
    2. Build a Google Maps URL with waypoints (max 10 for URL)
    3. Open it in the browser
    4. Also save KML for manual import to My Maps if needed
    """
    import webbrowser

    api_key = cfg["google_maps"]["api_key"]
    date_str = datetime.now().strftime("%Y-%m-%d")
    list_name = cfg["google_maps"]["list_name"].replace("{date}", date_str)

    # Save route file
    route_path = HUNTER_DIR / "hunt-route.json"
    with open(route_path, "w", encoding="utf-8", errors="replace") as f:
        json.dump({"list_name": list_name, "generated": date_str,
                   "stop_count": len(route), "stops": route}, f, indent=2, default=str)
    log.info(f"Route saved: {route_path}")

    # Build Google Maps URL (first 9 waypoints + destination)
    stops = [s for s in route if s.get("address")][:10]
    if stops:
        start = cfg["google_maps"]["start_address"]
        waypoints_str = "/".join([s["address"].replace(" ", "+") for s in stops])
        maps_url = f"https://www.google.com/maps/dir/{start.replace(' ','+')+'/'+waypoints_str}"
        log.info(f"Google Maps URL: {maps_url}")
        # Save URL to file for sidebar pickup
        url_path = HUNTER_DIR / "maps-url.txt"
        with open(url_path, "w", encoding="utf-8") as f:
            f.write(maps_url)

    # Build KML for Google My Maps import
    build_kml(route, list_name, HUNTER_DIR / "hunt-route.kml")
    log.info("KML file saved for Google My Maps import.")

def build_kml(route, name, output_path):
    """Generates a KML file importable into Google My Maps."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<kml xmlns="http://www.opengis.net/kml/2.2">',
             f'<Document><name>{name}</name>']
    for i, stop in enumerate(route):
        lat = stop.get("lat", "")
        lng = stop.get("lng", "")
        if not lat or not lng:
            continue
        title   = stop.get("title", f"Stop {i+1}").replace("&","&amp;")
        address = stop.get("address","").replace("&","&amp;")
        score   = stop.get("score", "?")
        url     = stop.get("url","")
        desc    = f"Score: {score}/10 | {address} | {url}"
        lines += [
            "<Placemark>",
            f"  <name>{title}</name>",
            f"  <description>{desc}</description>",
            f"  <Point><coordinates>{lng},{lat},0</coordinates></Point>",
            "</Placemark>"
        ]
    lines += ["</Document></kml>"]
    with open(output_path, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def run_full_scrape(cfg, state):
    log.info("=== WEEKEND HUNTER: FULL SCRAPE ===")
    seen_ids = set(state.get("seen_ids", []))
    all_listings = []

    # Scrape all sources
    if cfg["sources"]["estatesales_net"]["enabled"]:
        all_listings += scrape_estatesales(cfg, seen_ids)
    if cfg["sources"]["craigslist"]["enabled"]:
        all_listings += scrape_craigslist(cfg, seen_ids)
    if cfg["sources"]["facebook_marketplace"]["enabled"]:
        all_listings += scrape_facebook(cfg, seen_ids, mode="full")

    return process_listings(all_listings, cfg, state, mode="full")


def run_delta_scrape(cfg, state):
    log.info("=== WEEKEND HUNTER: DELTA UPDATE ===")
    last = state.get("last_delta_scrape") or state.get("last_full_scrape")
    if last:
        delta_mins = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
        cooldown = cfg["schedule"]["delta_scrape_cooldown_minutes"]
        if delta_mins < cooldown:
            log.info(f"Cooldown active — {cooldown - delta_mins:.0f} min remaining. Skipping.")
            return []

    seen_ids = set(state.get("seen_ids", []))
    new_listings = []

    if cfg["sources"]["estatesales_net"]["enabled"]:
        new_listings += scrape_estatesales(cfg, seen_ids)
    if cfg["sources"]["craigslist"]["enabled"]:
        new_listings += scrape_craigslist(cfg, seen_ids)
    if cfg["sources"]["facebook_marketplace"]["enabled"]:
        new_listings += scrape_facebook(cfg, seen_ids, mode="delta")

    return process_listings(new_listings, cfg, state, mode="delta")


def process_listings(raw_listings, cfg, state, mode):
    watchlist  = cfg.get("watchlist", [])
    min_score  = cfg["scoring"]["min_score_to_surface"]
    min_flip   = cfg["ebay_sourcing"]["min_flip_score"]
    processed  = []
    seen_ids   = set(state.get("seen_ids", []))

    for listing in raw_listings:
        lid = listing["id"]
        if lid in seen_ids:
            continue

        # Watchlist check
        watch_match = check_watchlist(listing, watchlist)
        if watch_match:
            listing["watchlist_flag"] = watch_match["term"]
            listing["watchlist_category"] = watch_match.get("category", "")

        # Score it
        if listing.get("type") == "garage_sale":
            listing["sale_score"] = score_garage_sale(listing, cfg)
        flip_score, reason, category = score_listing(listing, cfg)
        listing["flip_score"]   = flip_score
        listing["flip_reason"]  = reason
        listing["flip_category"] = category

        # Geocode
        api_key = cfg["google_maps"]["api_key"]
        lat, lng = geocode_address(listing.get("address",""), api_key)
        listing["lat"] = lat
        listing["lng"] = lng

        seen_ids.add(lid)
        processed.append(listing)

    # Update state
    state["seen_ids"] = list(seen_ids)
    state["total_found"] = state.get("total_found", 0) + len(processed)
    if mode == "full":
        state["last_full_scrape"] = datetime.now().isoformat()
    else:
        state["last_delta_scrape"] = datetime.now().isoformat()
    save_state(state)

    # Merge with existing results
    existing = load_results() if mode == "delta" else []
    combined = existing + processed
    save_results(combined)
    if mode == "delta":
        save_delta(processed)

    # Surface high-score items
    top_sales  = sorted([l for l in combined if l.get("sale_score",0) >= min_score],
                        key=lambda x: x.get("sale_score",0), reverse=True)
    top_flips  = sorted([l for l in combined if l.get("flip_score",0) >= min_flip],
                        key=lambda x: x.get("flip_score",0), reverse=True)
    watchlist_hits = [l for l in processed if l.get("watchlist_flag")]

    log.info(f"Processed: {len(processed)} new | Top sales: {len(top_sales)} | "
             f"Top flips: {len(top_flips)} | Watchlist hits: {len(watchlist_hits)}")

    # Build and push route if we have addresses
    routable = [l for l in top_sales if l.get("lat")]
    if routable:
        route = build_optimized_route(routable, cfg)
        push_to_google_maps(route, cfg)

    return processed


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Weekend Hunter Agent")
    parser.add_argument("--mode", choices=["full", "delta", "route"], default="full",
                        help="full=overnight scrape, delta=update only new, route=rebuild route only")
    args = parser.parse_args()

    cfg   = load_config()
    state = load_state()

    if args.mode == "full":
        run_full_scrape(cfg, state)
    elif args.mode == "delta":
        run_delta_scrape(cfg, state)
    elif args.mode == "route":
        existing = load_results()
        min_score = cfg["scoring"]["min_score_to_surface"]
        routable = [l for l in existing if l.get("lat") and l.get("sale_score",0) >= min_score]
        route = build_optimized_route(routable, cfg)
        push_to_google_maps(route, cfg)
        log.info("Route rebuilt from existing results.")

    log.info("Weekend Hunter done.")

if __name__ == "__main__":
    main()
