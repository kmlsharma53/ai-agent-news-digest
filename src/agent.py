"""Core agent loop: think → tool call → observe → repeat."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any

from .tools import TOOL_DEFINITIONS, execute_tool
from .memory import AgentMemory


MAX_TURNS = 15  # Safety limit on agent loop iterations

SYSTEM_PROMPT = """You are an autonomous AI agent that researches and reports on AI agent news for software developers.

You have tools to search news, read articles, check trending topics, and access your persistent memory.

YOUR WORKFLOW:
1. First, check your memory to see what you've already reported (avoid repeats)
2. Search for the latest AI agent news across multiple queries
3. Check trending topics to see what's hot right now
4. Read specific articles that look important to get more details
5. Save important observations to memory for future sessions
6. Synthesize everything into your final output

YOU DECIDE:
- What queries to search for (don't just use one — try multiple angles)
- Which articles are worth reading in detail
- What comparisons are interesting to make
- What trends to highlight based on your memory of past sessions
- What notes to save for next time

FOCUS ON:
- AI agent frameworks & SDKs (LangChain, CrewAI, AutoGen, Claude Agent SDK, OpenAI Agents, etc.)
- Developer tools (Cursor, Claude Code, Copilot, Devin, Windsurf, etc.)
- Protocols & standards (MCP, Agent Protocol, A2A, etc.)
- Benchmarks & comparisons (SWE-bench, agent evals)
- Multi-agent orchestration & agentic patterns

Be autonomous. Make your own decisions about what to investigate. Don't just list news — analyze, compare, and provide developer-focused insights."""


def _call_claude_with_tools(
    messages: list[dict],
    system: str,
    tools: list[dict],
    api_key: str,
) -> dict:
    """Call Claude API with tool_use support. Returns the full response."""
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": system,
        "tools": tools,
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        if hasattr(e, "read"):
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Claude API error: {e} - {body}") from e
        raise RuntimeError(f"Claude API error: {e}") from e


def run_agent(
    task: str,
    api_key: str,
    memory: AgentMemory,
    verbose: bool = False,
    max_turns: int = MAX_TURNS,
) -> str:
    """
    Run the agent loop.

    The agent autonomously decides which tools to call, observes results,
    and keeps going until it produces a final text response.

    Returns the final text output from the agent.
    """
    today = datetime.now().strftime("%B %d, %Y")
    user_message = f"[Date: {today}]\n\n{task}"

    messages: list[dict] = [
        {"role": "user", "content": user_message},
    ]

    turn = 0
    while turn < max_turns:
        turn += 1

        if verbose:
            print(f"\n--- Agent Turn {turn}/{max_turns} ---")

        # Call Claude with tools
        response = _call_claude_with_tools(
            messages=messages,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            api_key=api_key,
        )

        stop_reason = response.get("stop_reason", "")
        content_blocks = response.get("content", [])

        # Collect text output and tool calls from this turn
        text_parts: list[str] = []
        tool_calls: list[dict] = []

        for block in content_blocks:
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(block)

        # If the agent is thinking out loud, show it in verbose mode
        if verbose and text_parts:
            for text in text_parts:
                print(f"  [think] {text[:200]}{'...' if len(text) > 200 else ''}")

        # If no tool calls, the agent is done — return final text
        if stop_reason == "end_turn" and not tool_calls:
            return "\n".join(text_parts)

        # Process tool calls
        if tool_calls:
            # Add the assistant's response (with tool_use blocks) to messages
            messages.append({"role": "assistant", "content": content_blocks})

            # Execute each tool and collect results
            tool_results: list[dict] = []
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_input = tc.get("input", {})
                tool_id = tc["id"]

                if verbose:
                    print(f"  [tool] {tool_name}({json.dumps(tool_input, default=str)[:100]})")

                result = execute_tool(tool_name, tool_input, memory)

                if verbose:
                    preview = result[:150].replace("\n", " ")
                    print(f"  [result] {preview}{'...' if len(result) > 150 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                })

            # Send tool results back to Claude
            messages.append({"role": "user", "content": tool_results})
        else:
            # stop_reason is "end_turn" but we already handled that above
            # This handles edge cases
            return "\n".join(text_parts) if text_parts else "Agent completed without output."

    return "Agent reached maximum turns without producing a final response."


def run_digest(api_key: str, memory: AgentMemory, verbose: bool = False) -> str:
    """Run the agent with a digest task."""
    return run_agent(
        task=(
            "Generate today's AI Agent Developer News Digest.\n\n"
            "1. Check your memory for what was reported recently\n"
            "2. Search for the latest news using multiple queries\n"
            "3. Check trending topics\n"
            "4. Read 2-3 of the most important articles in detail\n"
            "5. Save noteworthy observations to memory\n"
            "6. Produce a digest with these sections:\n"
            "   - **Top Stories**: 3-5 most important items with why they matter\n"
            "   - **Framework & Tool Updates**: changes to agent frameworks/tools\n"
            "   - **Comparison Spotlight**: compare competing tools/approaches from the news\n"
            "   - **Developer Takeaways**: 3-5 actionable insights\n"
            "   - **Worth Watching**: emerging trends to follow\n\n"
            "Be autonomous — decide what to search, what to read, what to compare."
        ),
        api_key=api_key,
        memory=memory,
        verbose=verbose,
    )


def run_compare(tool1: str, tool2: str, api_key: str, memory: AgentMemory, verbose: bool = False) -> str:
    """Run the agent with a comparison task."""
    return run_agent(
        task=(
            f"Compare these two AI agent tools/frameworks: **{tool1}** vs **{tool2}**\n\n"
            f"1. Check memory for any past notes about {tool1} or {tool2}\n"
            f"2. Search for recent news about both tools\n"
            f"3. Read 1-2 relevant articles for deeper context\n"
            f"4. Save any important findings to memory\n"
            f"5. Produce a comparison covering:\n"
            f"   - **Purpose & Use Case**\n"
            f"   - **Key Differences** (architecture, approach)\n"
            f"   - **Developer Experience** (setup, docs, community)\n"
            f"   - **When to Use Which**\n"
            f"   - **Recent Momentum** (based on news and trends)\n"
        ),
        api_key=api_key,
        memory=memory,
        verbose=verbose,
    )


def run_ask(question: str, api_key: str, memory: AgentMemory, verbose: bool = False) -> str:
    """Run the agent with a free-form question."""
    return run_agent(
        task=(
            f"{question}\n\n"
            "Use your tools to research this question:\n"
            "- Search for relevant recent news\n"
            "- Check memory for past context\n"
            "- Read articles if needed for detail\n"
            "- Give a practical, developer-focused answer"
        ),
        api_key=api_key,
        memory=memory,
        verbose=verbose,
    )
