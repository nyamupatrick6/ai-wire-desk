"""
Takes raw items and asks Claude to:
  - assign each to one desk/category
  - write a one-line, neutral summary
  - flag whether it looks like a significant/"breaking" item

Batches items to keep prompts small. Requires ANTHROPIC_API_KEY in the
environment (set as a GitHub Actions secret — see README.md).
"""
import json
import os
import re
import sys

import anthropic

MODEL = os.environ.get("AI_WIRE_MODEL", "claude-sonnet-5")
BATCH_SIZE = 15

CATEGORIES = [
    "Model Releases",
    "Funding & Business",
    "Research",
    "Tools & Products",
    "Policy & Safety",
    "Community & Commentary",
]

SYSTEM_PROMPT = f"""You are a wire-desk editor for an AI industry news aggregator.
For each item you're given (title + source + url), do three things:
1. Assign it to exactly one desk from this fixed list: {", ".join(CATEGORIES)}.
2. Write a single neutral, factual sentence (under 25 words) summarizing what
   the item is about, based only on its title — do not invent details.
3. Set "signal" to true only if the title suggests genuinely significant news
   (a major model release, large funding round, notable policy action) and
   false otherwise.

Respond ONLY with a JSON array, one object per input item, in the same order,
each shaped exactly like:
{{"id": "<id>", "category": "<one of the desks>", "summary": "<one sentence>", "signal": true|false}}

No prose, no markdown fences, no commentary — JSON array only."""


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def _clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def summarize_batch(client, items):
    payload = [
        {"id": it["id"], "title": it["title"], "source": it["source"]} for it in items
    ]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload)}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        results = json.loads(_clean_json(text))
        by_id = {r["id"]: r for r in results if "id" in r}
        return by_id
    except Exception as e:
        print(f"  ! summarize batch failed: {e}", file=sys.stderr)
        return {}


def summarize_items(items):
    """items: list of raw item dicts. Returns the same items enriched with
    category/summary/signal fields."""
    if not items:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ! ANTHROPIC_API_KEY not set — falling back to uncategorized items", file=sys.stderr)
        for it in items:
            it.setdefault("category", "Community & Commentary")
            it.setdefault("summary", it["title"])
            it.setdefault("signal", False)
        return items

    client = anthropic.Anthropic(api_key=api_key)
    enriched = []
    for batch in _chunks(items, BATCH_SIZE):
        results = summarize_batch(client, batch)
        for it in batch:
            r = results.get(it["id"])
            if r:
                it["category"] = r.get("category", "Community & Commentary")
                it["summary"] = r.get("summary", it["title"])
                it["signal"] = bool(r.get("signal", False))
            else:
                it["category"] = "Community & Commentary"
                it["summary"] = it["title"]
                it["signal"] = False
            enriched.append(it)
    return enriched


if __name__ == "__main__":
    from fetch_sources import fetch_all

    raw = fetch_all()[:5]
    print(json.dumps(summarize_items(raw), indent=2))
