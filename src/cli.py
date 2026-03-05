"""CLI interface for the AI Agent News Digest."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from .agent import run_digest, run_compare, run_ask
from .fetcher import fetch_all_news
from .memory import AgentMemory


BANNER = r"""
  _   ___   _                  _     _  _
 /_\ |_ _| /_\  __ _ ___ _ _ | |_  | \| |_____ __ _____
/ _ \ | | / _ \/ _` / -_) ' \|  _| | .` / -_) V  V (_-<
/_/ \_\___/_/ \_\__, \___|_||_|\__| |_|\_\___|\_/\_//__/
                |___/
    Autonomous AI Agent Developer News Digest
"""


def _get_api_key() -> str:
    """Get Anthropic API key from environment."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)
    return key


def _save_output(content: str, prefix: str = "digest", output_dir: str = "output") -> str:
    """Save output to a dated file."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"{prefix}-{date_str}.md")
    with open(filepath, "w") as f:
        f.write(f"# AI Agent News - {date_str}\n\n")
        f.write(content)
    return filepath


def cmd_digest(args: argparse.Namespace) -> None:
    """Run the agent to produce a daily digest."""
    print(BANNER)
    print(f"Agent starting for {datetime.now().strftime('%B %d, %Y')}...\n")

    api_key = _get_api_key()
    memory = AgentMemory()

    print("The agent will autonomously:")
    print("  1. Check memory for past reports")
    print("  2. Search multiple news sources")
    print("  3. Analyze trending topics")
    print("  4. Read important articles in detail")
    print("  5. Generate the digest\n")

    result = run_digest(api_key, memory, verbose=args.verbose)

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)

    if args.save:
        filepath = _save_output(result, prefix="digest")
        print(f"\nSaved to: {filepath}")


def cmd_compare(args: argparse.Namespace) -> None:
    """Run the agent to compare two tools."""
    print(f"\nAgent comparing: {args.tool1} vs {args.tool2}\n")

    api_key = _get_api_key()
    memory = AgentMemory()

    result = run_compare(args.tool1, args.tool2, api_key, memory, verbose=args.verbose)

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)

    if args.save:
        filepath = _save_output(result, prefix="compare")
        print(f"\nSaved to: {filepath}")


def cmd_ask(args: argparse.Namespace) -> None:
    """Run the agent with a free-form question."""
    question = " ".join(args.question)
    print(f"\nAgent researching: {question}\n")

    api_key = _get_api_key()
    memory = AgentMemory()

    result = run_ask(question, api_key, memory, verbose=args.verbose)

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)


def cmd_fetch(args: argparse.Namespace) -> None:
    """Just fetch and display raw news items (no agent, no API key needed)."""
    print("\nFetching AI agent news...\n")
    news = fetch_all_news(verbose=True)

    if not news:
        print("No relevant news found.")
        return

    print(f"\n{'=' * 60}")
    print(f"Found {len(news)} articles:\n")
    for i, item in enumerate(news, 1):
        print(f"{i:2d}. [{item.source}]")
        print(f"    {item.title}")
        print(f"    {item.url}")
        if item.summary:
            print(f"    {item.summary[:120]}...")
        print()


def cmd_memory(args: argparse.Namespace) -> None:
    """View or manage agent memory."""
    memory = AgentMemory()

    if args.clear:
        import shutil
        if os.path.exists(memory.memory_dir):
            shutil.rmtree(memory.memory_dir)
        print("Memory cleared.")
        return

    entries = memory.get_recent(days=30)
    reported = memory.get_reported_count()

    print(f"\nAgent Memory (last 30 days)")
    print(f"Reported articles: {reported}")
    print(f"Memory entries: {len(entries)}\n")

    if entries:
        for entry in entries:
            date = entry["date"][:10]
            print(f"  [{date}] ({entry['category']}) {entry['note']}")
    else:
        print("  No memories yet. Run a digest to start building memory.")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="agent-news",
        description="Autonomous AI Agent News Digest - powered by Claude with tool use.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show agent thinking and tool calls")
    parser.add_argument("--save", action="store_true", help="Save output to file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # digest command
    sub_digest = subparsers.add_parser("digest", help="Agent generates today's daily digest")
    sub_digest.set_defaults(func=cmd_digest)

    # compare command
    sub_compare = subparsers.add_parser("compare", help="Agent compares two AI agent tools")
    sub_compare.add_argument("tool1", help="First tool/framework (e.g., langchain)")
    sub_compare.add_argument("tool2", help="Second tool/framework (e.g., crewai)")
    sub_compare.set_defaults(func=cmd_compare)

    # ask command
    sub_ask = subparsers.add_parser("ask", help="Ask the agent a question")
    sub_ask.add_argument("question", nargs="+", help="Your question")
    sub_ask.set_defaults(func=cmd_ask)

    # fetch command (no agent)
    sub_fetch = subparsers.add_parser("fetch", help="Just fetch raw news (no agent)")
    sub_fetch.set_defaults(func=cmd_fetch)

    # memory command
    sub_memory = subparsers.add_parser("memory", help="View or manage agent memory")
    sub_memory.add_argument("--clear", action="store_true", help="Clear all memory")
    sub_memory.set_defaults(func=cmd_memory)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
