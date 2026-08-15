# AI Wire Desk

A self-updating AI-news wire desk. A scheduled job pulls fresh items from RSS
feeds, Reddit, and Hacker News, has Claude sort them into desks (Model
Releases, Funding & Business, Research, Tools & Products, Policy & Safety,
Community & Commentary) and write a one-line summary for each, then commits
the result as `data/latest.json`. A static page (`index.html`) reads that
file and renders the report — no server needed.

## How it works

```
scripts/fetch_sources.py   → pulls raw items from sources.py (RSS + Reddit + HN)
scripts/summarize.py       → sends new items to Claude for category + one-line summary
scripts/build_report.py    → merges with recent history, writes data/latest.json
                              + an archived timestamped copy in data/archive/
.github/workflows/update.yml → runs build_report.py every ~20 min, commits the result
index.html + assets/       → static frontend that fetches data/latest.json
```

Items are kept on the live report for 72 hours (`RETENTION_HOURS` in
`build_report.py`) — older ones stay in `data/archive/` permanently.

## Setup

1. **Create the repo.** Push these files to a new GitHub repository.
2. **Add your Anthropic API key as a secret.**
   Repo → Settings → Secrets and variables → Actions → New repository secret
   → name it `ANTHROPIC_API_KEY`, paste a key from
   [console.anthropic.com](https://console.anthropic.com).
   *(Without this, the workflow still runs and files items — they just won't
   be categorized/summarized, and land under "Community & Commentary" with
   the raw title as the summary.)*
3. **Enable GitHub Pages.**
   Repo → Settings → Pages → Source: **Deploy from a branch** → Branch:
   `main` / `(root)`. Your site will be live at
   `https://<your-username>.github.io/<repo-name>/`.
4. **Enable the workflow.** Actions tab → enable workflows if prompted. The
   job runs automatically on the schedule in `update.yml`; you can also
   trigger it manually via Actions → "Update AI Wire Desk" → Run workflow.
5. **First run.** Kick off one manual run so `data/latest.json` has content
   before you share the link.

## Running locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/build_report.py
python -m http.server 8000   # then open http://localhost:8000
```

## Adding or changing sources

Edit `scripts/sources.py`:
- `RSS_FEEDS` — any standard RSS/Atom feed URL.
- `REDDIT_SUBREDDITS` — subreddit names, pulled via Reddit's public
  read-only JSON endpoint (no API key needed, but keep the list short and
  don't poll too aggressively).
- `HN_QUERIES` — search terms sent to the free Hacker News Algolia API.

**X/Twitter and YouTube** aren't included by default because reliable
pulling needs a paid/keyed API. If you have access:
- X: use the X API v2 recent-search endpoint, add a fetch function in
  `fetch_sources.py` mirroring `fetch_reddit()`, store the bearer token as
  another repo secret, and pass it through in `update.yml`.
- YouTube: use the YouTube Data API v3 `search.list` endpoint the same way,
  with a `YOUTUBE_API_KEY` secret.

## Adjusting categories

Edit the `CATEGORIES` list and `SYSTEM_PROMPT` in `scripts/summarize.py`, and
mirror any renamed categories in `CATEGORY_ORDER` in `assets/app.js`.

## Notes

- The workflow's cron schedule is best-effort — GitHub may delay runs
  during high load, so "every 20 minutes" is approximate, same as most
  scheduled-run setups on GitHub Actions.
- The frontend is plain HTML/CSS/JS with no build step, so it can be
  deployed to GitHub Pages directly from the repo root.
