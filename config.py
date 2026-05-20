import os
from dotenv import load_dotenv

# Always resolve paths relative to this file, not the working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

# How often the scheduler polls tracked items (seconds)
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Path to the SQLite database file — absolute so it works from any cwd
DB_PATH: str = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "watches.db"))
