# Weekend Hunter — How To Use

## First Time Setup (do these ONCE)

1. **Double-click `INSTALL-DEPS.bat`**
   - Installs the Python packages the agent needs
   - Takes about 30 seconds, then close the window

2. **Double-click `REGISTER-TASK.bat`**
   - Sets up the automatic Friday 11pm scrape
   - Just double-click it, no admin needed

3. **Add your Google Maps API key**
   - Go to: https://console.cloud.google.com
   - Create a project, enable "Geocoding API" and "Directions API"
   - Copy your key into `weekend-hunter-config.json`
   - Find the line that says: "api_key": ""
   - Paste your key between the quotes
   - (The agent still works without this — just no route optimization)

4. **Add items to your watchlist**
   - Open `weekend-hunter-config.json`
   - Find the "watchlist" section
   - Add anything you or your son are hunting
   - Already has: blender, roblox, sports cards, vinyl, vintage clothing, bass guitar

---

## Every Weekend

**Friday night:** The scraper runs automatically at 11pm.
Nothing to do — just let it run overnight.

**Saturday/Sunday morning:**
- Open the sidebar widget: `weekend-hunter-widget.html`
- See your top-scored sales and flip opportunities
- Click **"Open Route"** to get your Google Maps itinerary

**While you're out:**
- Double-click `run-delta.bat` (or hit Update Now in the widget)
- Picks up any last-minute sales posted that morning
- Adds new stops to your route

---

## The Files Explained

| File | What it does |
|------|-------------|
| `INSTALL-DEPS.bat` | One-time install of Python packages |
| `REGISTER-TASK.bat` | One-time setup of Friday night auto-scrape |
| `RESTART-BRIDGE.bat` | Restart the studio bridge if the widget can't connect |
| `run-full-scrape.bat` | Run a full scrape manually anytime |
| `run-delta.bat` | Quick update — only new listings since last run |
| `OPEN-MAPS-ROUTE.bat` | Opens your optimized route in Google Maps |
| `weekend-hunter-widget.html` | Dashboard — view results, scores, watchlist hits |
| `hunt-results.json` | All scraped listings (auto-generated) |
| `hunt-delta.json` | Just the new listings from last update |
| `hunt-route.kml` | Import this into Google My Maps manually if needed |
| `maps-url.txt` | The Google Maps URL for your current route |

---

## Watchlist
Items in the watchlist get **flagged immediately** regardless of score.
Edit `weekend-hunter-config.json` to add/remove items.
Current watchlist: blender, roblox, sports cards, vinyl records, vintage clothing, bass guitar

---

## Scoring
- **Sale Score 1-10**: How worth visiting a garage sale is
  - Shows sales scored 6 or higher
- **Flip Score 1-10**: How good an eBay flip opportunity is
  - Shows flips scored 7 or higher

---

## Troubleshooting

**Widget shows nothing:** Run `run-full-scrape.bat` first to populate results.

**Facebook scraping blocked:** Facebook blocks scrapers sometimes.
- Try running during off-peak hours
- The agent will skip Facebook and still get EstateSales + Craigslist

**Route not opening:** Make sure `push_to_maps.py` runs — double-click `OPEN-MAPS-ROUTE.bat`

**Bridge not responding:** Double-click `RESTART-BRIDGE.bat`
