# AI Agent News Digest

CLI tool that fetches, compares, and shares daily AI agent developer news. Powered by Claude.

## What it does

- Aggregates AI agent news from Hacker News, Reddit, Google News, and Dev.to
- Filters for developer-relevant content (frameworks, SDKs, tools, benchmarks)
- Uses Claude to generate a daily digest with comparisons and insights
- Can compare specific tools head-to-head (e.g., LangChain vs CrewAI)
- Supports scheduled daily runs at 7 AM

## Setup

```bash
# Clone the repo
git clone <your-repo-url>
cd ai-agent-news-digest

# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Install
pip install -e .
```

## Usage

### Generate today's digest
```bash
agent-news digest
agent-news digest --save        # save to output/ directory
agent-news digest --verbose     # show fetch details
```

### Compare two tools
```bash
agent-news compare langchain crewai
agent-news compare "claude code" cursor
agent-news compare autogen langgraph
```

### Ask a question
```bash
agent-news ask "What is the best agent framework for multi-agent orchestration?"
agent-news ask "How does MCP work?"
```

### Just fetch raw news
```bash
agent-news fetch
```

### Run without installing
```bash
python main.py digest
python main.py compare langchain crewai
```

## Schedule daily at 7 AM

### Option 1: macOS LaunchAgent (recommended)

```bash
# Copy the provided plist
cp com.agent-news.daily.plist ~/Library/LaunchAgents/
# Edit it to set your ANTHROPIC_API_KEY and paths
# Then load it:
launchctl load ~/Library/LaunchAgents/com.agent-news.daily.plist
```

### Option 2: Cron job

```bash
crontab -e
# Add this line (adjust paths):
0 7 * * * cd /path/to/ai-agent-news-digest && ANTHROPIC_API_KEY=your-key python main.py digest --save
```

## Sources tracked

- Hacker News (AI agent + LLM agent queries)
- Reddit (r/MachineLearning, r/LocalLLaMA)
- Google News (AI agent developer tools)
- Dev.to (AI agent articles)

## License

MIT
