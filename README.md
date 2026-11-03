<div align="center">

# 🤖 RH Agent

**Talk to your Robinhood account in plain English — a Claude tool-use agent.**

![Python](https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-tool%20use-d97757?style=flat-square)
![Swift](https://img.shields.io/badge/QuickPlayer-SwiftUI-f05138?style=flat-square&logo=swift&logoColor=white)

</div>

---

> ⚠️ **Places real orders.** Use at your own risk. This is not financial advice.

## 💬 What it does

A command-line chat loop where Claude drives a set of Robinhood tools via [`robin_stocks`](https://github.com/jmfernandes/robin_stocks):

```
You: what's my portfolio look like?
Agent: Total equity $…  Top positions: …
You: buy 1 share of AAPL
Agent: Confirm: market buy 1 AAPL at ~$… ?
```

| Tool | Description |
|------|-------------|
| `get_portfolio_summary` | Equity and buying power |
| `get_positions` | Current holdings |
| `get_quote` | Latest price for a symbol |
| `buy_stock` / `sell_stock` | Market orders |
| `get_open_orders` / `cancel_order` | Manage pending orders |

**Guardrails** are built into the system prompt: confirm before ordering, never exceed the stated amount, ask when intent is ambiguous, and always report the order ID and state.

## 🚀 Quick start

```bash
pip install -r requirements.txt
cp .env.example .env      # add Robinhood + Anthropic credentials
python main.py
```

## 🧰 Also in this repo

| Path | What |
|------|------|
| `video_downloader.py` | Grab every video on a page — `yt-dlp` first, Playwright browser extraction as fallback. Flags: `--list`, `--low`, `--browser-only`, `-o DIR` |
| `QuickPlayer/` | A tiny SwiftUI macOS audio player with drag-and-drop playlist. Build with `./build.sh` |

## 🗂️ Layout

```
main.py     chat loop
agent.py    Claude tool-use loop + system prompt
tools.py    Robinhood tool definitions & handlers
auth.py     login / logout
```

---

<div align="center"><sub>Made by <a href="https://github.com/emmanuelhuff7">@emmanuelhuff7</a></sub></div>
