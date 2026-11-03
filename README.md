# RH Agent

A command-line chat agent for a Robinhood account. Claude gets a few tools built on [robin_stocks](https://github.com/jmfernandes/robin_stocks) and decides when to call them. This places real orders.

```
You: how's my portfolio?
You: buy 1 share of AAPL
```

Tools: portfolio summary, positions, quote, market buy, market sell, list open orders, cancel order. The system prompt tells the model to confirm before ordering, never exceed the amount you give, and report the order ID and state afterward.

## Setup

```
pip install -r requirements.txt
cp .env.example .env     # Robinhood login and Anthropic API key
python main.py
```

- `main.py` chat loop
- `agent.py` tool-use loop and system prompt
- `tools.py` Robinhood functions
- `auth.py` login / logout

## Other things in here

- `video_downloader.py` downloads the videos on a page, trying yt-dlp first and falling back to a Playwright browser for custom players. Options: `--list`, `--low`, `--browser-only`, `-o DIR`.
- `QuickPlayer/` is a small SwiftUI audio player for macOS with drag-and-drop. Build with `QuickPlayer/build.sh`.
