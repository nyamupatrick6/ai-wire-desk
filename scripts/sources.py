"""
Source list for the AI Wire Desk aggregator.
Edit this file to add/remove where the desk pulls from.
No API keys required for any source in this file.
"""

# Standard RSS/Atom feeds — news outlets, company blogs, research feeds.
RSS_FEEDS = [
    # Company / lab blogs
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml"},
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss/"},

    # Tech press covering AI
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica AI", "url": "https://arstechnica.com/ai/feed/"},
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},

    # Research
    {"name": "arXiv cs.AI", "url": "http://export.arxiv.org/rss/cs.AI"},
    {"name": "arXiv cs.CL", "url": "http://export.arxiv.org/rss/cs.CL"},
    {"name": "arXiv cs.LG", "url": "http://export.arxiv.org/rss/cs.LG"},
]

# Reddit subs, pulled via public read-only JSON endpoints (no auth needed).
REDDIT_SUBREDDITS = [
    "artificial",
    "MachineLearning",
    "singularity",
    "OpenAI",
    "LocalLLaMA",
]

# Hacker News, via the free Algolia HN Search API (no auth needed).
HN_QUERIES = ["AI", "LLM", "Claude", "GPT", "machine learning"]

# YouTube and X/Twitter need paid/keyed APIs to pull reliably and are left
# out by default to keep this repo runnable with zero paid credentials.
# See README.md "Adding more sources" for how to wire them in if you have keys.
