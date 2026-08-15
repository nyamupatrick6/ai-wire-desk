"""
Pulls raw items from every source in sources.py and normalizes them into:
{
  "id": "<sha1 of url>",
  "title": str,
  "url": str,
  "source": str,          # human readable source name
  "source_type": str,     # "rss" | "reddit" | "hackernews"
  "published_at": str,    # ISO 8601, best-effort
  "discovered_at": str,   # ISO 8601, when THIS run found it
}
"""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone

import feedparser
import requests

from sources import RSS_FEEDS, REDDIT_SUBREDDITS, HN_QUERIES

USER_AGENT = "ai-wire-desk/1.0 (+https://github.com/) personal AI news aggregator"
TIMEOUT = 15


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _item_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _safe_get(url, headers=None, params=None):
    try:
        r = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, **(headers or {})},
            params=params,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  ! request failed: {url} -> {e}", file=sys.stderr)
        return None


def fetch_rss():
    items = []
    for feed in RSS_FEEDS:
        print(f"[rss] {feed['name']}")
        try:
            parsed = feedparser.parse(feed["url"], agent=USER_AGENT)
        except Exception as e:
            print(f"  ! parse failed: {feed['url']} -> {e}", file=sys.stderr)
            continue
        for entry in parsed.entries[:25]:
            url = entry.get("link")
            title = entry.get("title")
            if not url or not title:
                continue
            published = None
            for key in ("published", "updated", "created"):
                if entry.get(key):
                    published = entry.get(key)
                    break
            items.append(
                {
                    "id": _item_id(url),
                    "title": title.strip(),
                    "url": url,
                    "source": feed["name"],
                    "source_type": "rss",
                    "published_at": published or _now_iso(),
                    "discovered_at": _now_iso(),
                }
            )
    return items


def fetch_reddit():
    items = []
    for sub in REDDIT_SUBREDDITS:
        print(f"[reddit] r/{sub}")
        r = _safe_get(f"https://www.reddit.com/r/{sub}/new.json", params={"limit": 20})
        if r is None:
            continue
        try:
            data = r.json()
        except Exception:
            continue
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            url = post.get("url_overridden_by_dest") or f"https://reddit.com{post.get('permalink', '')}"
            title = post.get("title")
            if not url or not title:
                continue
            created = post.get("created_utc")
            published = (
                datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                if created
                else _now_iso()
            )
            items.append(
                {
                    "id": _item_id(url),
                    "title": title.strip(),
                    "url": url,
                    "source": f"r/{sub}",
                    "source_type": "reddit",
                    "published_at": published,
                    "discovered_at": _now_iso(),
                }
            )
        time.sleep(1)  # be polite to reddit's public endpoint
    return items


def fetch_hackernews():
    items = []
    for query in HN_QUERIES:
        print(f"[hn] query={query}")
        r = _safe_get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={"query": query, "tags": "story", "hitsPerPage": 20},
        )
        if r is None:
            continue
        try:
            data = r.json()
        except Exception:
            continue
        for hit in data.get("hits", []):
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            title = hit.get("title")
            if not url or not title:
                continue
            items.append(
                {
                    "id": _item_id(url),
                    "title": title.strip(),
                    "url": url,
                    "source": "Hacker News",
                    "source_type": "hackernews",
                    "published_at": hit.get("created_at") or _now_iso(),
                    "discovered_at": _now_iso(),
                }
            )
    return items


def fetch_all():
    all_items = fetch_rss() + fetch_reddit() + fetch_hackernews()
    # de-dupe by id (url hash), keep first occurrence
    seen = set()
    deduped = []
    for item in all_items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        deduped.append(item)
    print(f"\nFetched {len(all_items)} raw items, {len(deduped)} after de-dupe.")
    return deduped


if __name__ == "__main__":
    items = fetch_all()
    print(json.dumps(items[:5], indent=2))
