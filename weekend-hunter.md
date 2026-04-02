# Weekend Hunter Agent

## Purpose
Weekend garage sale and eBay sourcing intelligence agent. Scrapes multiple sources,
scores listings for sale quality and flip potential, flags watchlist items, geocodes
addresses, optimizes a driving route, and outputs a Google Maps-ready itinerary.

## Status
- **Active** — registered in scrape-registry.json
- Full scrape: Friday 11pm via Task Scheduler (WeekendHunterFullScrape)
- Delta update: manual trigger via run-delta.bat or sidebar widget Update button

## Sources
| Source | Method | Notes |
|--------|--------|-------|
| Facebook Marketplace | Selenium (logged-in Chrome profile) | garage_sale keyword search |
| Facebook Groups | Selenium | group keyword search |
| EstateSales.net | requests + BeautifulSoup | radius search from Atwood TN |
| Craigslist | requests + BeautifulSoup | Nashville garage section |

## Outputs
| File | Description |
|------|-------------|
| `weekend-hunter/hunt-results.json` | All scraped listings with scores |
| `weekend-hunter/hunt-delta.json` | New listings since last scrape |
| `weekend-hunter/hunt-route.json` | Optimized route stops |
| `weekend-hunter/hunt-route.kml` | KML for Google My Maps import |
| `weekend-hunter/maps-url.txt` | Google Maps directions URL (auto-opens) |
| `weekend-hunter/hunter.log` | Run log |

## Scoring
- **sale_score 1-10**: Garage sale visit worthiness (diversity, keywords, photos, address present)
- **flip_score 1-10**: eBay flip potential (vintage/brand keywords, Claude reasoning when available)
- Surfaces: sale_score >= 6, flip_score >= 7
- Watchlist items: flagged regardless of score

## Watchlist
Configured in `weekend-hunter-config.json` under `watchlist[]`.
Add terms + category to flag specific items you're hunting.

## Route
- Google Maps Directions API (requires API key in config)
- Waypoint-optimized driving route from Atwood TN start
- KML fallback for manual My Maps import if no API key

## Dependencies
```
pip install selenium requests beautifulsoup4 --break-system-packages
```
- Chrome + chromedriver (for Facebook scraping)
- Google Maps API key (Geocoding + Directions APIs)

## CLAUDE.md Rules Applied
- Hamilton: Task Scheduler registered with TTL
- Codd: 95% confidence gate on address/date extraction (blank-over-wrong)
- Shannon: Handoff summary written to hunt-state.json

## Files
- `weekend-hunter/weekend_hunter_agent.py` — main agent
- `weekend-hunter/weekend-hunter-widget.html` — Opera sidebar widget
- `weekend-hunter/run-full-scrape.bat` — Friday night trigger
- `weekend-hunter/run-delta.bat` — manual delta trigger
- `weekend-hunter/register-weekend-hunter-task.ps1` — Task Scheduler setup
- `weekend-hunter-config.json` — all settings, watchlist, scoring weights
