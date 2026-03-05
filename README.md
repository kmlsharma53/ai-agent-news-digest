# AI Agent News Digest

An **autonomous AI agent** that researches, compares, and shares daily AI agent developer news. Built with Claude's tool_use API.

## How it works

This is a real AI agent, not a pipeline. It runs an **agentic loop**:

```
think → pick a tool → execute → observe result → think again → repeat
```

The agent autonomously decides:
- **What to search** - crafts its own queries across multiple sources
- **What to read** - picks articles worth reading in detail
- **What to compare** - identifies competing tools and frameworks
- **What to remember** - saves observations to persistent memory for future sessions
- **What to report** - synthesizes findings into a developer-focused digest

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Agent Loop                      │
│  think → tool_use → observe → think → ...       │
├─────────────────────────────────────────────────┤
│  Tools (agent picks from these):                │
│  ┌──────────────┐  ┌──────────────────────┐     │
│  │ search_news  │  │ get_trending_topics  │     │
│  │ fetch_rss    │  │ read_article         │     │
│  │ recall_memory│  │ save_memory          │     │
│  └──────────────┘  └──────────────────────┘     │
├─────────────────────────────────────────────────┤
│  Memory (persistent across sessions)            │
│  - Past digests, trends, notes, reported titles │
└─────────────────────────────────────────────────┘
```

## Setup

```bash
git clone https://github.com/kmlsharma53/ai-agent-news-digest.git
cd ai-agent-news-digest
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Daily digest (agent mode)
```bash
python3 main.py digest              # agent runs autonomously
python3 main.py digest -v           # watch the agent think and use tools
python3 main.py digest --save       # save to output/
```

### Compare two tools (agent mode)
```bash
python3 main.py compare langchain crewai
python3 main.py compare "claude code" cursor -v
```

### Ask a question (agent mode)
```bash
python3 main.py ask "What is MCP and why should I care?"
python3 main.py ask "Best framework for multi-agent orchestration?"
```

### Raw news fetch (no agent, no API key)
```bash
python3 main.py fetch
```

### View agent memory
```bash
python3 main.py memory              # see what the agent remembers
python3 main.py memory --clear      # wipe memory
```

## Schedule daily at 7 AM

```bash
crontab -e
# Add:
0 7 * * * cd /path/to/ai-agent-news-digest && ANTHROPIC_API_KEY=your-key python3 main.py digest --save
```

Or use the included macOS LaunchAgent:
```bash
# Edit com.agent-news.daily.plist to set your API key
cp com.agent-news.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.agent-news.daily.plist
```

## Verbose mode (-v)

With `-v`, you can watch the agent's thought process:

```
--- Agent Turn 1/15 ---
  [think] Let me start by checking my memory for recent reports...
  [tool] recall_memory({})
  [result] No relevant memories found. (last 7 days)

--- Agent Turn 2/15 ---
  [think] This is a fresh start. Let me search for the latest news...
  [tool] search_news({"query": "ai agent framework release 2025"})
  [result] [{"title": "CrewAI v2 launches with...", ...

--- Agent Turn 3/15 ---
  [tool] get_trending_topics({})
  [result] Trending: mcp ############ (12), claude ######### (9)...

--- Agent Turn 4/15 ---
  [think] MCP is trending heavily. Let me read more about it...
  [tool] read_article({"url": "https://..."})
  ...
```

## License

MIT
