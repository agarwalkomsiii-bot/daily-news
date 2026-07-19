"""
Daily News Digest Builder
--------------------------
Pulls headlines + summaries straight from trusted news organizations'
own official RSS feeds (no AI-generated summaries, no guessing) and
builds a static index.html page.

Run manually with:  python fetch_news.py
GitHub Actions runs this automatically every day (see .github/workflows/daily-news.yml)
"""

import feedparser
import json
import re
import html
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. CONFIGURE YOUR SOURCES HERE
# ---------------------------------------------------------------------------
# Add, remove, or swap feeds freely. Format: ("Source Name", "RSS URL")

FEEDS = {
    "World": [
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("The Guardian World", "https://www.theguardian.com/world/rss"),
    ],
    "India": [
        ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),
        ("The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
        ("NDTV", "https://feeds.feedburner.com/ndtvnews-top-stories"),
    ],
    "Business": [
        ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml"),
        ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
        ("Livemint", "https://www.livemint.com/rss/news"),
    ],
    "Technology": [
        ("BBC Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml"),
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("Gadgets360", "https://www.gadgets360.com/rss/news"),
    ],
    "Sports": [
        ("BBC Sport", "http://feeds.bbci.co.uk/sport/rss.xml"),
        ("ESPN Cricinfo", "https://www.espncricinfo.com/rss/content/story/feeds/0.xml"),
        ("NDTV Sports", "https://feeds.feedburner.com/ndtvsports-latest"),
    ],
}

MAX_ITEMS_PER_FEED = 6
MAX_ITEMS_PER_CATEGORY = 12
SUMMARY_MAX_CHARS = 220

# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------

def clean_text(raw):
    """Strip HTML tags/entities out of RSS descriptions."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)      # remove tags
    text = html.unescape(text)                # decode entities like &amp;
    text = re.sub(r"\s+", " ", text).strip()   # collapse whitespace
    return text


def truncate(text, max_chars=SUMMARY_MAX_CHARS):
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "…"


def get_published(entry):
    """Try several fields feeds use for publish date; fall back gracefully."""
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def fetch_category(source_list):
    items = []
    for source_name, url in source_list:
        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                print(f"  [warn] Could not read feed: {source_name} ({url})")
                continue
            for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
                title = clean_text(entry.get("title", "")).strip()
                summary = truncate(clean_text(entry.get("summary", "") or entry.get("description", "")))
                link = entry.get("link", "")
                if not title or not link:
                    continue
                items.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": source_name,
                    "published": get_published(entry).isoformat(),
                })
        except Exception as e:
            print(f"  [error] {source_name}: {e}")
            continue

    # Remove near-duplicate headlines (same title from multiple outlets)
    seen_titles = set()
    unique_items = []
    for item in items:
        key = item["title"].lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        unique_items.append(item)

    # Newest first
    unique_items.sort(key=lambda x: x["published"], reverse=True)
    return unique_items[:MAX_ITEMS_PER_CATEGORY]


# ---------------------------------------------------------------------------
# 3. HTML RENDERING
# ---------------------------------------------------------------------------

def render_html(data, generated_at):
    sections_html = ""
    for category, items in data.items():
        if not items:
            continue
        cards = ""
        for item in items:
            cards += f"""
            <a class="card" href="{item['link']}" target="_blank" rel="noopener noreferrer">
                <div class="card-source">{item['source']}</div>
                <h3 class="card-title">{item['title']}</h3>
                <p class="card-summary">{item['summary']}</p>
            </a>
            """
        sections_html += f"""
        <section class="category">
            <h2>{category}</h2>
            <div class="card-grid">
                {cards}
            </div>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily News Digest</title>
<style>
    :root {{
        --bg: #f5f6f8;
        --card-bg: #ffffff;
        --text: #1a1a1a;
        --muted: #6b7280;
        --accent: #b91c1c;
        --border: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
    }}
    header {{
        background: var(--text);
        color: white;
        padding: 24px 16px;
        text-align: center;
    }}
    header h1 {{
        margin: 0 0 4px 0;
        font-size: 28px;
    }}
    header p {{
        margin: 0;
        color: #b8b8b8;
        font-size: 14px;
    }}
    main {{
        max-width: 1000px;
        margin: 0 auto;
        padding: 24px 16px 60px;
    }}
    .category {{
        margin-bottom: 36px;
    }}
    .category h2 {{
        border-left: 4px solid var(--accent);
        padding-left: 10px;
        font-size: 20px;
        margin-bottom: 14px;
    }}
    .card-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 14px;
    }}
    .card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 16px;
        text-decoration: none;
        color: var(--text);
        display: block;
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }}
    .card:hover {{
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }}
    .card-source {{
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--accent);
        margin-bottom: 6px;
    }}
    .card-title {{
        font-size: 15px;
        margin: 0 0 6px 0;
        line-height: 1.35;
    }}
    .card-summary {{
        font-size: 13px;
        color: var(--muted);
        margin: 0;
        line-height: 1.4;
    }}
    footer {{
        text-align: center;
        color: var(--muted);
        font-size: 12px;
        padding: 20px;
    }}
</style>
</head>
<body>
<header>
    <h1>📰 Daily News Digest</h1>
    <p>Auto-updated every day &middot; Last updated: {generated_at} UTC</p>
</header>
<main>
    {sections_html}
</main>
<footer>
    Headlines and summaries pulled directly from each source's own RSS feed. Tap any card to read the full article on the original site.
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------------------------

def main():
    print("Fetching news...")
    data = {}
    for category, sources in FEEDS.items():
        print(f"Category: {category}")
        data[category] = fetch_category(sources)
        print(f"  -> {len(data[category])} items")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    # Save raw data for reference/debugging
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": generated_at, "data": data}, f, indent=2, ensure_ascii=False)

    # Build the site
    html_output = render_html(data, generated_at)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print("Done. index.html and data/news.json updated.")


if __name__ == "__main__":
    main()
