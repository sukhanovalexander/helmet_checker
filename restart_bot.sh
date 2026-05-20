#!/bin/bash
SCRIPT_NAME="bot"
BOT_DIR="/root/library-bot"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$BOT_DIR/logs/bot_$TIMESTAMP.out"

mkdir -p "$BOT_DIR/logs"

pkill -9 -f "$SCRIPT_NAME.py"
sleep 2

nohup "$BOT_DIR/.venv/bin/python3" "$BOT_DIR/$SCRIPT_NAME.py" >> "$LOG_FILE" 2>&1 &
echo "Bot started, logging to $LOG_FILE"
