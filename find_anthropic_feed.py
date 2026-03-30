import urllib.request
import re
import json

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; StudioIntelAgent/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

# Check Anthropic endpoints
urls = [
    "https://www.anthropic.com/news",
    "https://www.anthropic.com/research",
    "https://www.anthropic.com/sitemap.xml",
    "https://www.anthropic.com/sitemap-0.xml",
]

for url in urls:
    try:
        content = fetch(url)
        feeds = re.findall(r'(?:href|src)=["\']([^"\']*(?:rss|feed|atom)[^"\']*)["\']', content, re.IGNORECASE)
        articles = list(set(re.findall(r'href="(/news/[^"?#]{5,})"', content)))
        print("OK: " + url + " (" + str(len(content)) + " bytes)")
        if feeds:
            print("  Feed refs found: " + str(feeds[:5]))
        print("  Article hrefs: " + str(len(articles)))
        if articles:
            print("  Sample: " + str(articles[:4]))
    except Exception as e:
        print("FAIL: " + url + " -> " + str(e))

# Also check YouTube API key validity
print("")
print("Checking YouTube API key...")
try:
    with open("G:/My Drive/Projects/_studio/studio-config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    key = config.get("youtube_api_key", "")
    print("Key present: " + str(bool(key)) + " | First 12 chars: " + key[:12])
    # Test a simple API call
    test_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=AI+news+today&type=video&maxResults=3&key=" + key
    result = fetch(test_url)
    data = json.loads(result)
    if "items" in data:
        print("YouTube API: WORKING - returned " + str(len(data["items"])) + " results")
        for item in data["items"]:
            print("  - " + item["snippet"]["title"][:80])
    elif "error" in data:
        print("YouTube API ERROR: " + str(data["error"]["message"]))
except Exception as e:
    print("YouTube check failed: " + str(e))
