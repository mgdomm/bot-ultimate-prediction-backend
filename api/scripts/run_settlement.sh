#!/bin/bash

BASE_DIR="/home/mgdomm1988/bot-ultimate-prediction/api"
VENV_DIR="$BASE_DIR/.venv"
LOG_DIR="$BASE_DIR/logs"

mkdir -p "$LOG_DIR"

source "$VENV_DIR/bin/activate"

python "$BASE_DIR/scripts/settle_bets.py" >> "$LOG_DIR/settlement.log" 2>&1
