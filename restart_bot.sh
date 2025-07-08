#!/bin/bash

# Script to automatically restart the Telegram bot if it stops

LOG_FILE="bot_restart.log"
BOT_SCRIPT="telegram_bot.py"
PID_FILE="telegram_bot.pid"
MAX_RESTARTS=10
RESTART_COUNT=0

echo "$(date): Bot restart monitor started" >> $LOG_FILE

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    # Check if bot is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "$(date): Bot is running (PID: $PID)" >> $LOG_FILE
            sleep 300  # Check every 5 minutes
            continue
        else
            echo "$(date): Bot process not found, PID file exists but process is dead" >> $LOG_FILE
            rm -f $PID_FILE
        fi
    else
        echo "$(date): PID file not found, bot is not running" >> $LOG_FILE
    fi
    
    # Bot is not running, restart it
    RESTART_COUNT=$((RESTART_COUNT + 1))
    echo "$(date): Restarting bot (attempt $RESTART_COUNT/$MAX_RESTARTS)" >> $LOG_FILE
    
    python3 $BOT_SCRIPT &
    sleep 30  # Wait for bot to start
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "$(date): Bot successfully restarted (PID: $PID)" >> $LOG_FILE
            RESTART_COUNT=0  # Reset counter on successful restart
        else
            echo "$(date): Bot restart failed" >> $LOG_FILE
        fi
    else
        echo "$(date): Bot restart failed - no PID file created" >> $LOG_FILE
    fi
    
    sleep 60  # Wait before next check
done

echo "$(date): Maximum restart attempts reached. Monitor exiting." >> $LOG_FILE