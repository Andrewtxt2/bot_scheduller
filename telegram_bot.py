#!/usr/bin/env python3
"""
Telegram Promotional Message Bot

Automatically sends promotional messages to specified Telegram groups
on a regular schedule (every 4 hours).
"""

import time
import requests
import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093207171:AAEOmGvkSz0Z6nKb3vl0r3Iz2MyZjoWQqEA')

# Target group IDs
GROUP_IDS = [
    -1002111810768,
    -1002098871252,
    -1001927958845,
    -1001508552538
]

# Promotional message
MESSAGE = """🔔 Наші інші корисні Telegram-групи:

🏘 Нерухомість: @sofiannproperty  
🚗 Авто: @sofiaautosell  
📰 Новини: @sofianewnews  
💬 Чат громади: @sbpbchatnn  
📢 Оголошення: @sbpb_ogoloshennya  
💼 Робота: @worksofia

✅ Долучайся, щоб нічого не пропустити!
"""

# Schedule configuration
SEND_INTERVAL = 4 * 60 * 60  # 4 hours in seconds


def send_message(chat_id, text):
    """
    Send a message to a specific Telegram chat/group.
    
    Args:
        chat_id (int): The chat ID to send the message to
        text (str): The message text to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Message sent successfully to chat {chat_id}")
            return True
        else:
            error_description = result.get('description', 'Unknown error')
            error_code = result.get('error_code', 'Unknown code')
            logger.error(f"Failed to send message to chat {chat_id}: Code {error_code} - {error_description}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error when sending to chat {chat_id}: {str(e)}")
        return False
    except ValueError as e:
        logger.error(f"JSON decode error for chat {chat_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when sending to chat {chat_id}: {str(e)}")
        return False


def send_to_all_groups():
    """
    Send promotional message to all configured groups.
    
    Returns:
        tuple: (successful_sends, total_groups)
    """
    logger.info("Starting message broadcast to all groups")
    successful_sends = 0
    
    for chat_id in GROUP_IDS:
        if send_message(chat_id, MESSAGE):
            successful_sends += 1
        # Small delay between messages to avoid rate limiting
        time.sleep(1)
    
    logger.info(f"Broadcast completed: {successful_sends}/{len(GROUP_IDS)} messages sent successfully")
    return successful_sends, len(GROUP_IDS)


def validate_bot_token():
    """
    Validate the bot token by making a test API call.
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            logger.info(f"Bot token validated successfully. Bot: @{bot_info.get('username', 'unknown')}")
            return True
        else:
            logger.error(f"Invalid bot token: {result.get('description', 'Unknown error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during token validation: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        return False


def main():
    """
    Main function to run the bot continuously.
    """
    logger.info("=" * 50)
    logger.info("Telegram Promotional Bot Starting")
    logger.info("=" * 50)
    
    # Validate bot token before starting
    if not validate_bot_token():
        logger.error("Bot token validation failed. Please check your BOT_TOKEN environment variable.")
        sys.exit(1)
    
    logger.info(f"Bot will send messages to {len(GROUP_IDS)} groups every {SEND_INTERVAL/3600} hours")
    
    # Send initial message
    send_to_all_groups()
    
    # Main loop
    try:
        while True:
            next_send_time = datetime.now().timestamp() + SEND_INTERVAL
            next_send_formatted = datetime.fromtimestamp(next_send_time).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Next message broadcast scheduled for: {next_send_formatted}")
            
            # Wait for the specified interval
            time.sleep(SEND_INTERVAL)
            
            # Send messages to all groups
            send_to_all_groups()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
