#!/usr/bin/env python3
"""
Cron-like message sender for Telegram bot
Runs independently and checks scheduled times every minute
"""

import time
import requests
import os
import logging
import json
from datetime import datetime, timedelta
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_sender.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093207171:AAGoIRsBcpBXPfLRz4RvXv3wMwdmEib6jn4')

# Target group IDs
GROUP_IDS = [
    -1002111810768,
    -1002098871252,
    -1001927958845,
    -1001508552538,
    -1001988059903
]

# Promotional message
MESSAGE = """🔔 Наші інші корисні Telegram-групи:

🏘 Нерухомість: @sofiannproperty
🚗 Авто: @autosellkyiv
📰 Новини: @sofianewnews
💬 Чат громади Софіївської Борщагівки: @sbpbchatnn
📢 Оголошення: @sbpb_ogoloshennya
💼 Робота: @worksofia
🏙 Чат ЖК "У-квартал": @neoffukvartal
📍 Новини Вишневого, Крюківщини: @kryuvysh
🔎 Канал з вакансіями: @robota_borshchahivka_kyiv

✅ Долучайся, щоб нічого не пропустити!

"""

# Schedule in GMT+3
SCHEDULE_TIMES = ["09:00", "14:45", "17:00", "21:00"]
LAST_SEND_FILE = "last_send_cron.txt"

def send_message(chat_id, text):
    """Send message to Telegram chat"""
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
            logger.error(f"Failed to send message to chat {chat_id}: {error_description}")
            return False
    except Exception as e:
        logger.error(f"Error sending to chat {chat_id}: {str(e)}")
        return False

def send_to_all_groups():
    """Send message to all groups"""
    logger.info("Starting cron message broadcast")
    successful_sends = 0
    
    for chat_id in GROUP_IDS:
        if send_message(chat_id, MESSAGE):
            successful_sends += 1
        time.sleep(1)  # Rate limiting
    
    logger.info(f"Cron broadcast completed: {successful_sends}/{len(GROUP_IDS)} messages sent")
    return successful_sends

def get_gmt_plus3_time():
    """Get current time in GMT+3"""
    utc_now = datetime.utcnow()
    gmt_plus3 = utc_now + timedelta(hours=3)
    return gmt_plus3

def should_send_now():
    """Check if we should send message now"""
    current_time = get_gmt_plus3_time()
    current_time_str = current_time.strftime("%H:%M")
    
    # Check if current time matches schedule
    if current_time_str not in SCHEDULE_TIMES:
        return False
    
    # Check if we already sent today at this time
    try:
        if os.path.exists(LAST_SEND_FILE):
            with open(LAST_SEND_FILE, 'r') as f:
                last_send_data = json.load(f)
                
            last_send_time = datetime.fromisoformat(last_send_data['timestamp'])
            last_send_schedule = last_send_data['schedule_time']
            
            # If we sent within the last 10 minutes at this scheduled time, skip
            time_diff = (current_time - last_send_time).total_seconds()
            if time_diff < 600 and last_send_schedule == current_time_str:
                return False
    except:
        pass
    
    return True

def record_send_time():
    """Record when we sent the message"""
    current_time = get_gmt_plus3_time()
    data = {
        'timestamp': current_time.isoformat(),
        'schedule_time': current_time.strftime("%H:%M")
    }
    
    try:
        with open(LAST_SEND_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to record send time: {e}")

def main():
    """Main cron function"""
    logger.info("Cron sender started")
    
    while True:
        try:
            current_time = get_gmt_plus3_time()
            logger.info(f"Checking time: {current_time.strftime('%H:%M')} GMT+3")
            
            if should_send_now():
                logger.info("Time matches schedule, sending messages...")
                success_count = send_to_all_groups()
                
                if success_count > 0:
                    record_send_time()
                    logger.info(f"Successfully sent {success_count} messages")
                else:
                    logger.error("Failed to send any messages")
            
            # Sleep for 60 seconds before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Cron sender stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in cron loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()