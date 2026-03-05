"""CLI interface for the AI Agent News Digest."""

import argparse
import os
import sys
from datetime import datetime

from .fetcher import fetch_all_news
from .analyzer import generate_daily_digest, compare_tools, ask_agent


BANNER = r"""
  _   ___   _                  _     _  _
 /_\ |_ _| /_\  __ _ ___ _ _ | |_  | \| |_____ __ _____
/ _ \ | | / _ \/ _` / -_) ' \|  _| | .` / -_) V  V (_-<
/_/ \_\___/_/ \_\__, \___|_||_|\__| |_|\_\___|\_/\_//__/
                |___/
       Daily AI Agent Developer News Digest
"""


def _get_api_key() -> str:
    """Get Anthropic API key from environment."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
        print("Or create a .env file (see .env.example)")
        sys.exit(1)
    return key


def _save_digest(content: str, output_dir: str = "output") -> str:
    """Save digest to a dated file."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"digest-{date_str}.md")
    with open(filepath, "w") as f:
        f.write(f"# AI Agent News Digest - {date_str}\n\n")
        f.write(content)
    return filepath


def cmd_digest(args: argparse.Namespace) -> None:
    """Run the daily digest command."""
    print(BANNER)
    print(f"Generating digest for {datetime.now().strftime('%B %d, %Y')}...\n")

    print("Step 1/2: Fetching news from multiple sources...")
    news = fetch_all_news(verbose=args.verbose)
    print(f"  Found {len(news)} relevant articles\n")

    if not news:
        print("No relevant AI agent news found today.")
        return

    print("Step 2/2: Analyzing with Claude...\n")
    api_key = _get_api_key()
    digest = generate_daily_digest(news, api_key)

    print("=" * 60)
    print(digest)
    print("=" * 60)

    if args.save:
        filepath = _save_digest(digest)
        print(f"\nDigest saved to: {filepath}")


def cmd_compare(args: argparse.Namespace) -> None:
    """Run the compare command."""
    print(f"\nComparing: {args.tool1} vs {args.tool2}\n")

    print("Fetching recent news for context...")
    news = fetch_all_news(verbose=args.verbose)

    api_key = _get_api_key()
    result = compare_tools(args.tool1, args.tool2, news, api_key)

    print("=" * 60)
    print(result)
    print("=" * 60)

    if args.save:
        filepath = _save_digest(result)
        print(f"\nComparison saved to: {filepath}")


def cmd_ask(args: argparse.Namespace) -> None:
    """Run the ask command."""
    question = " ".join(args.question)
    print(f"\nQuestion: {question}\n")

    print("Fetching recent news for context...")
    news = fetch_all_news(verbose=args.verbose)

    api_key = _get_api_key()
    answer = ask_agent(question, news, api_key)

    print("=" * 60)
    print(answer)
    print("=" * 60)


def cmd_fetch(args: argparse.Namespace) -> None:
    """Just fetch and display raw news items."""
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


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="agent-news",
        description="AI Agent News Digest - Daily AI agent developer news, compared and analyzed.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--save", action="store_true", help="Save output to file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # digest command
    sub_digest = subparsers.add_parser("digest", help="Generate today's daily digest")
    sub_digest.set_defaults(func=cmd_digest)

    # compare command
    sub_compare = subparsers.add_parser("compare", help="Compare two AI agent tools")
    sub_compare.add_argument("tool1", help="First tool/framework (e.g., langchain)")
    sub_compare.add_argument("tool2", help="Second tool/framework (e.g., crewai)")
    sub_compare.set_defaults(func=cmd_compare)

    # ask command
    sub_ask = subparsers.add_parser("ask", help="Ask a question about AI agents")
    sub_ask.add_argument("question", nargs="+", help="Your question")
    sub_ask.set_defaults(func=cmd_ask)

    # fetch command
    sub_fetch = subparsers.add_parser("fetch", help="Just fetch and list raw news")
    sub_fetch.set_defaults(func=cmd_fetch)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
