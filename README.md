# 📰 Daily News Digest

A self-updating news website. A script runs automatically every day, pulls
headlines and summaries directly from trusted news outlets' own RSS feeds,
and rebuilds `index.html`. GitHub Pages then serves that file as a live website.

No API keys. No AI-generated summaries. Every headline links back to the
original article on the source's own site.

## Files
- `fetch_news.py` — fetches feeds and builds `index.html`
- `requirements.txt` — the one Python package needed (`feedparser`)
- `.github/workflows/daily-news.yml` — the automation (runs daily + can be triggered manually)
- `data/news.json` — raw data snapshot, kept for reference/debugging

## Changing sources
Open `fetch_news.py` and edit the `FEEDS` dictionary near the top. Each entry is
`("Display Name", "RSS URL")`. Add, remove, or swap them freely — for example,
to change the local-news country, replace the feeds under `"India"`.

## Running locally (optional)
```
pip install -r requirements.txt
python fetch_news.py
```
Then open `index.html` in a browser.

Full setup instructions for GitHub are in the chat where this was built.
