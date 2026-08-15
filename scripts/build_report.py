"""
Orchestrator: fetch -> summarize only the new items -> merge with recent
history -> write data/latest.json (what the site reads) and archive a
timestamped copy under data/archive/.

Run this on a schedule (see .github/workflows/update.yml).
"""
import json
import os
from datetime import datetime, timedelta, timezone

from fetch_sources import fetch_all
from summarize import summarize_items

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

RETENTION_HOURS = 72  # how far back items are kept on the live report


def _load_latest():
    if not os.path.exists(LATEST_PATH):
        return {"generated_at": None, "items": []}
    with open(LATEST_PATH, "r") as f:
        return json.load(f)


def _parse_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def build():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    previous = _load_latest()
    known_ids = {it["id"] for it in previous["items"]}

    print("Fetching sources...")
    raw_items = fetch_all()
    new_items = [it for it in raw_items if it["id"] not in known_ids]
    print(f"{len(new_items)} new items to summarize (of {len(raw_items)} fetched).")

    enriched_new = summarize_items(new_items)

    combined = previous["items"] + enriched_new

    # drop anything older than the retention window, based on discovered_at
    cutoff = datetime.now(timezone.utc) - timedelta(hours=RETENTION_HOURS)
    combined = [it for it in combined if _parse_dt(it["discovered_at"]) >= cutoff]

    # newest first
    combined.sort(key=lambda it: _parse_dt(it["discovered_at"]), reverse=True)

    now = datetime.now(timezone.utc)
    report = {
        "generated_at": now.isoformat(),
        "item_count": len(combined),
        "new_this_run": len(enriched_new),
        "sources_checked": len({it["source"] for it in raw_items}),
        "items": combined,
    }

    with open(LATEST_PATH, "w") as f:
        json.dump(report, f, indent=2)

    archive_name = now.strftime("%Y-%m-%d_%H%M%S") + ".json"
    with open(os.path.join(ARCHIVE_DIR, archive_name), "w") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {LATEST_PATH} ({len(combined)} items, {len(enriched_new)} new).")


if __name__ == "__main__":
    build()
