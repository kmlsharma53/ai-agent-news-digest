"""Fetches AI agent developer news from multiple sources."""

from __future__ import annotations

import re
import urllib.request
import urllib.error
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    summary: str
    published: str


# RSS/Atom feeds focused on AI agents and developer tooling
FEEDS = [
    {
        "name": "Hacker News (AI)",
        "url": "https://hnrss.org/newest?q=ai+agent",
        "type": "rss",
    },
    {
        "name": "Hacker News (LLM Agents)",
        "url": "https://hnrss.org/newest?q=llm+agent",
        "type": "rss",
    },
    {
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/search.json?q=ai+agent&sort=new&restrict_sr=1&t=day",
        "type": "reddit",
    },
    {
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/search.json?q=agent&sort=new&restrict_sr=1&t=day",
        "type": "reddit",
    },
    {
        "name": "Google News (AI Agent Developer)",
        "url": "https://news.google.com/rss/search?q=AI+agent+developer+tools&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Dev.to (AI Agents)",
        "url": "https://dev.to/search/feed_content?per_page=10&search_fields=ai+agent&sort_by=published_at&sort_direction=desc&class_name=Article",
        "type": "devto",
    },
]

AGENT_KEYWORDS = [
    "ai agent", "llm agent", "autonomous agent", "agent framework",
    "langchain", "langgraph", "crewai", "autogen", "openai agent",
    "claude agent", "agent sdk", "tool use", "function calling",
    "multi-agent", "agentic", "mcp", "model context protocol",
    "agent protocol", "ai coding", "coding agent", "ai assistant",
    "copilot", "cursor", "claude code", "devin", "opendevin",
    "swe-agent", "agent benchmark",
]


def _is_relevant(title: str, summary: str) -> bool:
    """Check if a news item is relevant to AI agents for developers."""
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in AGENT_KEYWORDS)


def _parse_rss(xml_text: str, source_name: str) -> list[NewsItem]:
    """Parse RSS/Atom feed XML into NewsItem list."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # Handle RSS 2.0
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        desc = item.findtext("description", "")
        pub_date = item.findtext("pubDate", "")
        # Strip HTML tags from description
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:500]
        if title and _is_relevant(title, desc):
            items.append(NewsItem(
                title=title.strip(),
                url=link.strip(),
                source=source_name,
                summary=desc,
                published=pub_date,
            ))

    # Handle Atom feeds
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = entry.findtext("atom:title", "", ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        desc = entry.findtext("atom:summary", "", ns)
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:500]
        pub_date = entry.findtext("atom:updated", "", ns)
        if title and _is_relevant(title, desc):
            items.append(NewsItem(
                title=title.strip(),
                url=link.strip(),
                source=source_name,
                summary=desc,
                published=pub_date,
            ))

    return items[:10]


def _parse_reddit(json_text: str, source_name: str) -> list[NewsItem]:
    """Parse Reddit JSON search results."""
    items = []
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return items

    for post in data.get("data", {}).get("children", []):
        pd = post.get("data", {})
        title = pd.get("title", "")
        url = f"https://reddit.com{pd.get('permalink', '')}"
        selftext = pd.get("selftext", "")[:500]
        created = pd.get("created_utc", 0)
        pub_date = datetime.fromtimestamp(created).isoformat() if created else ""
        if title and _is_relevant(title, selftext):
            items.append(NewsItem(
                title=title,
                url=url,
                source=source_name,
                summary=selftext,
                published=pub_date,
            ))

    return items[:10]


def _parse_devto(json_text: str, source_name: str) -> list[NewsItem]:
    """Parse Dev.to API response."""
    items = []
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return items

    for article in data.get("result", []):
        title = article.get("title", "")
        path = article.get("path", "")
        url = f"https://dev.to{path}" if path else ""
        user = article.get("user", {}).get("username", "")
        pub_date = article.get("published_at_int", "")
        if title and _is_relevant(title, ""):
            items.append(NewsItem(
                title=title,
                url=url,
                source=f"{source_name} (@{user})" if user else source_name,
                summary="",
                published=str(pub_date),
            ))

    return items[:10]


def _fetch_url(url: str) -> str | None:
    """Fetch URL content with timeout and user-agent."""
    headers = {
        "User-Agent": "AIAgentNewsDigest/1.0 (Developer News Aggregator)"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  [warn] Failed to fetch {url}: {e}")
        return None


def fetch_all_news(verbose: bool = False) -> list[NewsItem]:
    """Fetch news from all configured sources and return relevant items."""
    all_items: list[NewsItem] = []

    for feed in FEEDS:
        if verbose:
            print(f"  Fetching from {feed['name']}...")

        content = _fetch_url(feed["url"])
        if not content:
            continue

        if feed["type"] == "rss":
            items = _parse_rss(content, feed["name"])
        elif feed["type"] == "reddit":
            items = _parse_reddit(content, feed["name"])
        elif feed["type"] == "devto":
            items = _parse_devto(content, feed["name"])
        else:
            continue

        if verbose:
            print(f"    Found {len(items)} relevant items")
        all_items.extend(items)

    # Deduplicate by title similarity
    seen_titles: set[str] = set()
    unique_items: list[NewsItem] = []
    for item in all_items:
        normalized = item.title.lower().strip()
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_items.append(item)

    return unique_items
