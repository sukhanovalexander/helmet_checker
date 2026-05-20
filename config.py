"""
Configuration — reads from environment variables.
Copy .env.example to .env and fill in your values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

# How often the scheduler polls tracked items (seconds)
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Path to the SQLite database file
DB_PATH: str = os.getenv("DB_PATH", "data/watches.db")
