# Library Availability Bot

Telegram bot that watches a library item page and notifies you when it becomes available.

## Project structure

```
library-bot/
├── bot.py                  # Entry point — starts bot + scheduler
├── config.py               # Env-var configuration
├── db.py                   # SQLite persistence layer
├── scheduler.py            # Background polling loop (every 60 s)
├── scrapers/
│   └── library.py          # Page fetch + XPath extraction  ← fill in here
├── handlers/
│   ├── add.py              # /add command + library-selection keyboard
│   ├── delete.py           # /delete command
│   └── check_now.py        # /check_now command
├── data/                   # SQLite DB lives here (git-ignored)
├── requirements.txt
└── .env.example
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in BOT_TOKEN
python bot.py
```

## What still needs filling in (`scrapers/library.py`)

| Constant | What it needs |
|---|---|
| `LIBRARY_NAME_XPATH` | XPath to each branch name in the availability table |
| `ROW_XPATH` | XPath to each `<tr>` in the availability table |
| `LIBRARY_CELL_INDEX` | Column index of the branch name cell |
| `STATUS_CELL_INDEX` | Column index of the status cell |
| `STATUS_AVAILABLE_PATTERN` | Text / class substring that means "available" |

## Commands

| Command | Description |
|---|---|
| `/add <url>` | Start tracking a library item URL |
| `/delete` | Remove an existing watch |
| `/check_now` | Immediately check all your watches |
