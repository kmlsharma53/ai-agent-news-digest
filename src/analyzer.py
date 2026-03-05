"""Uses Claude API to analyze, compare, and summarize AI agent news."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import os
from datetime import datetime

from .fetcher import NewsItem


SYSTEM_PROMPT = """You are an AI agent news analyst for software developers.
Your job is to analyze the latest news about AI agents, frameworks, and tools used by developers.

Focus on:
- New AI agent frameworks and SDKs (LangChain, CrewAI, AutoGen, Claude Agent SDK, OpenAI Agents, etc.)
- Updates to existing agent tools (Cursor, Claude Code, Copilot, Devin, etc.)
- Benchmarks and comparisons between agent frameworks
- New capabilities (tool use, MCP, function calling, multi-agent orchestration)
- Industry trends in agentic AI for developers

Provide practical, developer-focused insights. Be concise and actionable."""


def _call_claude(messages: list[dict], system: str, api_key: str) -> str:
    """Call Claude API and return the response text."""
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": system,
        "messages": messages,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        if hasattr(e, "read"):
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Claude API error: {e} - {body}") from e
        raise RuntimeError(f"Claude API error: {e}") from e


def generate_daily_digest(news_items: list[NewsItem], api_key: str) -> str:
    """Generate a daily digest comparing and analyzing AI agent news."""
    if not news_items:
        return "No relevant AI agent news found today. Check back tomorrow!"

    # Format news items for the prompt
    news_text = "\n\n".join(
        f"**{i+1}. [{item.source}] {item.title}**\n"
        f"   URL: {item.url}\n"
        f"   Published: {item.published}\n"
        f"   Summary: {item.summary[:300]}"
        for i, item in enumerate(news_items)
    )

    today = datetime.now().strftime("%B %d, %Y")

    user_message = f"""Here are today's ({today}) news items related to AI agents for developers:

{news_text}

Please create a daily digest with the following sections:

1. **Top Stories** - The 3-5 most important items and why they matter to developers
2. **Framework & Tool Updates** - Any updates to agent frameworks (LangChain, CrewAI, AutoGen, Claude SDK, etc.)
3. **Comparison Spotlight** - Compare any competing tools/approaches mentioned in the news
4. **Developer Takeaways** - 3-5 actionable insights for developers working with AI agents
5. **Worth Watching** - Emerging trends or early-stage projects to keep an eye on

Keep it concise and practical. Use bullet points. Total length should be under 800 words."""

    return _call_claude(
        messages=[{"role": "user", "content": user_message}],
        system=SYSTEM_PROMPT,
        api_key=api_key,
    )


def compare_tools(tool1: str, tool2: str, news_items: list[NewsItem], api_key: str) -> str:
    """Compare two specific AI agent tools/frameworks based on recent news."""
    relevant_news = [
        item for item in news_items
        if tool1.lower() in f"{item.title} {item.summary}".lower()
        or tool2.lower() in f"{item.title} {item.summary}".lower()
    ]

    news_context = ""
    if relevant_news:
        news_context = "\n\nRecent news context:\n" + "\n".join(
            f"- [{item.source}] {item.title}: {item.summary[:200]}"
            for item in relevant_news
        )

    user_message = f"""Compare these two AI agent tools/frameworks for developers:

**Tool 1:** {tool1}
**Tool 2:** {tool2}
{news_context}

Provide a comparison covering:
1. **Purpose & Use Case** - What each tool is designed for
2. **Key Differences** - Architecture, approach, capabilities
3. **Developer Experience** - Ease of setup, documentation, community
4. **When to Use Which** - Practical guidance for developers
5. **Recent Momentum** - Based on any recent news or trends

Keep it practical and under 500 words."""

    return _call_claude(
        messages=[{"role": "user", "content": user_message}],
        system=SYSTEM_PROMPT,
        api_key=api_key,
    )


def ask_agent(question: str, news_items: list[NewsItem], api_key: str) -> str:
    """Ask the agent any question about AI agents for developers."""
    news_context = ""
    if news_items:
        news_context = "\n\nRecent news for context:\n" + "\n".join(
            f"- [{item.source}] {item.title}"
            for item in news_items[:15]
        )

    user_message = f"""{question}
{news_context}

Answer from the perspective of a developer working with AI agents. Be practical and specific."""

    return _call_claude(
        messages=[{"role": "user", "content": user_message}],
        system=SYSTEM_PROMPT,
        api_key=api_key,
    )
