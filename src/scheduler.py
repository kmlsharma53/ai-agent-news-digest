"""Scheduler to run the digest daily at 7 AM."""

import time
import signal
import sys
from datetime import datetime, timedelta

from .fetcher import fetch_all_news
from .analyzer import generate_daily_digest


def _next_run_time(hour: int = 7, minute: int = 0) -> datetime:
    """Calculate the next run time for the given hour:minute."""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_scheduled(api_key: str, hour: int = 7, save: bool = True) -> None:
    """Run the digest on a schedule, executing daily at the specified hour."""
    import os

    running = True

    def handle_signal(signum, frame):
        nonlocal running
        print("\nShutting down scheduler...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print(f"Scheduler started. Will run daily at {hour:02d}:00")
    print("Press Ctrl+C to stop.\n")

    while running:
        next_run = _next_run_time(hour)
        wait_seconds = (next_run - datetime.now()).total_seconds()
        print(f"Next digest at: {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
              f"(in {wait_seconds/3600:.1f} hours)")

        # Sleep in small intervals so we can respond to signals
        while running and datetime.now() < next_run:
            time.sleep(min(60, max(0, (next_run - datetime.now()).total_seconds())))

        if not running:
            break

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Running daily digest...")

        try:
            news = fetch_all_news(verbose=True)
            if news:
                digest = generate_daily_digest(news, api_key)
                print("\n" + "=" * 60)
                print(digest)
                print("=" * 60 + "\n")

                if save:
                    output_dir = "output"
                    os.makedirs(output_dir, exist_ok=True)
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    filepath = os.path.join(output_dir, f"digest-{date_str}.md")
                    with open(filepath, "w") as f:
                        f.write(f"# AI Agent News Digest - {date_str}\n\n")
                        f.write(digest)
                    print(f"Saved to: {filepath}")
            else:
                print("No relevant news found today.")
        except Exception as e:
            print(f"Error generating digest: {e}")

    print("Scheduler stopped.")
