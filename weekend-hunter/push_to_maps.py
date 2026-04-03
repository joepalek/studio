"""
push_to_maps.py
===============
Standalone script that reads hunt-results.json and pushes the best
garage sales directly to Google Maps as an optimized route URL.
Opens the route in your default browser immediately.

Usage: python push_to_maps.py
"""

import json, webbrowser, sys
from pathlib import Path
from datetime import datetime

STUDIO  = Path("G:/My Drive/Projects/_studio")
HUNTER  = STUDIO / "weekend-hunter"
CONFIG  = STUDIO / "weekend-hunter-config.json"
RESULTS = HUNTER / "hunt-results.json"
URL_OUT = HUNTER / "maps-url.txt"

def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return json.load(f)

def build_maps_url(stops, origin):
    """Build a Google Maps directions URL from a list of addresses."""
    if not stops:
        return None
    # Google Maps URL supports up to 10 waypoints in the URL
    addrs = [s["address"].strip() for s in stops if s.get("address","").strip()]
    addrs = addrs[:9]  # max 9 waypoints + destination = 10 total
    if not addrs:
        return None
    encoded = [a.replace(" ", "+").replace(",", "%2C") for a in addrs]
    origin_enc = origin.replace(" ", "+")
    waypoints = "/".join(encoded)
    return f"https://www.google.com/maps/dir/{origin_enc}/{waypoints}/{origin_enc}"

def main():
    cfg = load_json(CONFIG)
    if not cfg:
        print("ERROR: Config not found at", CONFIG)
        sys.exit(1)

    results = load_json(RESULTS)
    if not results:
        print("No results yet. Run a scrape first:")
        print("  Double-click: weekend-hunter\\run-full-scrape.bat")
        sys.exit(0)

    origin      = cfg["google_maps"]["start_address"]
    min_score   = cfg["scoring"]["min_score_to_surface"]

    # Filter to high-score sales with addresses
    top_sales = [
        r for r in results
        if r.get("address","").strip()
        and (r.get("sale_score", 0) >= min_score or r.get("flip_score", 0) >= 7)
    ]
    top_sales.sort(key=lambda x: x.get("sale_score", 0), reverse=True)

    if not top_sales:
        print(f"No listings with addresses and score >= {min_score} found.")
        print("Try lowering min_score_to_surface in weekend-hunter-config.json")
        sys.exit(0)

    print(f"Found {len(top_sales)} high-score listings with addresses.")
    print(f"Building route from: {origin}")
    print()

    # Show the stops
    for i, s in enumerate(top_sales[:9], 1):
        score = s.get("sale_score", s.get("flip_score","?"))
        print(f"  Stop {i}: [{score}/10] {s.get('title','?')[:50]} — {s['address']}")

    url = build_maps_url(top_sales, origin)
    if not url:
        print("Could not build URL — no valid addresses found.")
        sys.exit(0)

    # Save URL
    with open(URL_OUT, "w", encoding="utf-8") as f:
        f.write(url)
    print()
    print("Route URL saved to:", URL_OUT)
    print()
    print("Opening Google Maps now...")
    webbrowser.open(url)
    print()
    print("Done! Your route is open in the browser.")
    print("Tip: Bookmark or share the Maps link from your browser for mobile use.")

if __name__ == "__main__":
    main()
