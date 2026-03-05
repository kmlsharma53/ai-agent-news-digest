"""Tool definitions that the agent can autonomously pick from."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from .fetcher import NewsItem, _fetch_url, _parse_rss, _parse_reddit, _parse_devto, _is_relevant
from .memory import AgentMemory


# ── Tool schemas for Claude tool_use API ─────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "search_news",
        "description": (
            "Search for AI agent news using a custom query. "
            "Searches Hacker News and Google News RSS feeds. "
            "Use this to find news about specific topics, frameworks, or tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'crewai release', 'mcp protocol update', 'langchain vs autogen')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_rss_feed",
        "description": (
            "Fetch articles from a specific RSS feed URL. "
            "Use this to get news from a particular source."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The RSS feed URL to fetch",
                },
                "source_name": {
                    "type": "string",
                    "description": "A label for this source (e.g., 'Hacker News')",
                },
            },
            "required": ["url", "source_name"],
        },
    },
    {
        "name": "read_article",
        "description": (
            "Fetch and read the text content of a web article URL. "
            "Use this to get more details about a specific news item. "
            "Returns the first ~3000 chars of the page text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The article URL to read",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "recall_memory",
        "description": (
            "Check what was reported in previous digests. "
            "Use this to avoid repeating old news and to identify trends. "
            "Returns past digest titles and any saved notes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional keyword to search memory for (e.g., 'langchain', 'mcp'). Leave empty to get recent history.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "save_memory",
        "description": (
            "Save a note or observation to persistent memory for future sessions. "
            "Use this to track trends, remember important findings, or note things to follow up on."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "The note to save (e.g., 'LangChain v0.3 released with breaking changes')",
                },
                "category": {
                    "type": "string",
                    "enum": ["trend", "release", "comparison", "followup"],
                    "description": "Category for the note",
                },
            },
            "required": ["note", "category"],
        },
    },
    {
        "name": "get_trending_topics",
        "description": (
            "Analyze which AI agent topics are trending right now based on "
            "Reddit and Hacker News activity. Returns topic frequency counts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool implementations ─────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Strip HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


def execute_tool(name: str, args: dict[str, Any], memory: AgentMemory) -> str:
    """Execute a tool by name and return the result as a string."""
    if name == "search_news":
        return _tool_search_news(args["query"])
    elif name == "fetch_rss_feed":
        return _tool_fetch_rss(args["url"], args["source_name"])
    elif name == "read_article":
        return _tool_read_article(args["url"])
    elif name == "recall_memory":
        return _tool_recall_memory(args.get("query", ""), memory)
    elif name == "save_memory":
        return _tool_save_memory(args["note"], args["category"], memory)
    elif name == "get_trending_topics":
        return _tool_trending_topics()
    else:
        return f"Unknown tool: {name}"


def _tool_search_news(query: str) -> str:
    """Search HN and Google News for a query."""
    encoded = urllib.request.quote(query)
    sources = [
        ("Hacker News", f"https://hnrss.org/newest?q={encoded}&count=15"),
        ("Google News", f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"),
    ]

    all_items: list[dict] = []
    for source_name, url in sources:
        content = _fetch_url(url)
        if not content:
            continue
        items = _parse_rss(content, source_name)
        for item in items[:8]:
            all_items.append({
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "summary": item.summary[:200],
                "published": item.published,
            })

    if not all_items:
        return f"No results found for query: {query}"

    return json.dumps(all_items, indent=2)


def _tool_fetch_rss(url: str, source_name: str) -> str:
    """Fetch and parse an RSS feed."""
    content = _fetch_url(url)
    if not content:
        return f"Failed to fetch RSS feed: {url}"

    items = _parse_rss(content, source_name)
    if not items:
        return f"No items found in feed: {url}"

    result = [
        {
            "title": item.title,
            "url": item.url,
            "summary": item.summary[:200],
            "published": item.published,
        }
        for item in items
    ]
    return json.dumps(result, indent=2)


def _tool_read_article(url: str) -> str:
    """Fetch and return article text content."""
    content = _fetch_url(url)
    if not content:
        return f"Failed to fetch article: {url}"

    # Basic extraction: strip HTML, take meaningful text
    text = _strip_html(content)
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Return first 3000 chars
    if len(text) > 3000:
        text = text[:3000] + "... [truncated]"

    return text if text else "Could not extract text content from this URL."


def _tool_recall_memory(query: str, memory: AgentMemory) -> str:
    """Recall from persistent memory."""
    if query:
        entries = memory.search(query)
    else:
        entries = memory.get_recent(days=7)

    if not entries:
        return "No relevant memories found." + (
            f" (searched for: {query})" if query else " (last 7 days)"
        )

    result = []
    for entry in entries:
        result.append(
            f"[{entry['date']}] ({entry['category']}) {entry['note']}"
        )

    return "\n".join(result)


def _tool_save_memory(note: str, category: str, memory: AgentMemory) -> str:
    """Save a note to persistent memory."""
    memory.add(note=note, category=category)
    return f"Saved to memory: [{category}] {note}"


def _tool_trending_topics() -> str:
    """Analyze trending AI agent topics from multiple sources."""
    # Fetch from multiple HN queries to get a breadth of topics
    queries = ["ai agent", "llm agent", "agentic", "mcp server", "coding agent"]
    topic_counts: dict[str, int] = {}

    keywords_to_track = [
        "langchain", "langgraph", "crewai", "autogen", "openai",
        "claude", "anthropic", "mcp", "cursor", "copilot", "devin",
        "multi-agent", "tool use", "function calling", "agent sdk",
        "agent protocol", "benchmark", "swe-bench", "open source",
        "autonomous", "coding agent", "claude code",
    ]

    for query in queries:
        encoded = urllib.request.quote(query)
        content = _fetch_url(f"https://hnrss.org/newest?q={encoded}&count=20")
        if not content:
            continue

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            continue

        for item in root.findall(".//item"):
            title = (item.findtext("title", "") + " " + item.findtext("description", "")).lower()
            for kw in keywords_to_track:
                if kw in title:
                    topic_counts[kw] = topic_counts.get(kw, 0) + 1

    if not topic_counts:
        return "Could not determine trending topics right now."

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    lines = ["Trending AI agent topics (by mention frequency):"]
    for topic, count in sorted_topics[:15]:
        bar = "#" * min(count, 20)
        lines.append(f"  {topic:<20s} {bar} ({count})")

    return "\n".join(lines)
