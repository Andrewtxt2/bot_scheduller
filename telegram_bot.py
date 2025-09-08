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
from datetime import datetime, timedelta
import schedule
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

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
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093207171:AAGoIRsBcpBXPfLRz4RvXv3wMwdmEib6jn4')

# Target group IDs
GROUP_IDS = [
    -1002111810768,
    -1002098871252,
    -1001927958845,
    -1001508552538,
    -1001988059903
]

# Health check server configuration
HEALTH_CHECK_PORT = 5000

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests for health check"""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Check if bot is properly configured
            bot_status = "healthy" if validate_bot_token() else "unhealthy"
            next_run = get_next_scheduled_time()
            
            response = {
                "status": "ok",
                "service": "telegram-promotional-bot",
                "bot_status": bot_status,
                "next_scheduled_run": next_run,
                "timezone": TIMEZONE,
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to reduce HTTP server logging noise"""
        pass


def start_health_check_server():
    """Start the health check HTTP server in a separate thread"""
    try:
        server = HTTPServer(('0.0.0.0', HEALTH_CHECK_PORT), HealthCheckHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"Health check server started on port {HEALTH_CHECK_PORT}")
        return server
    except Exception as e:
        logger.error(f"Failed to start health check server: {e}")
        return None


def find_available_port():
    """Find an available port for the health check server"""
    for port in range(5000, 5100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    return None


# Promotional message
MESSAGE = """🔔 Наші інші корисні Telegram-групи:

🏘 Нерухомість: @sofiannproperty  
🚗 Авто: @sofiaautosell  
📰 Новини: @sofianewnews  
💬 Чат громади Софіївської Борщагівки: @sbpbchatnn 
📢 Оголошення: @sbpb_ogoloshennya  
💼 Робота: @worksofia  
🏘 Чат ЖК "У-квартал": @neoffukvartal 
🏠 Новини Вишневого, Крюківщини @kryuvysh

✅ Долучайся, щоб нічого не пропустити!

"""

# Schedule configuration - specific times to send messages
# You can customize these times by changing the values below
# Format: "HH:MM" in 24-hour format
SCHEDULE_TIMES = [
    "09:00",  # 9:00 AM
    "14:45",  # 2:45 PM  
    "17:00",  # 5:00 PM
    "21:00"   # 9:00 PM
]

# Alternative schedule examples:
# For business hours only: ["09:00", "12:00", "15:00", "18:00"]
# For more frequent: ["08:00", "11:00", "14:00", "17:00", "20:00", "23:00"]
# For morning and evening: ["08:00", "20:00"]

# Advanced scheduling configuration
TIMEZONE = "GMT+3"  # Set your timezone (UTC, Europe/Kiev, America/New_York, etc.)
SCHEDULE_CONFIG_FILE = "schedule_config.json"


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
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Starting scheduled message broadcast at {current_time} to all groups")
    successful_sends = 0
    
    # Check if we already sent messages in the last minute to prevent duplicates
    last_send_file = 'last_send_time.txt'
    try:
        if os.path.exists(last_send_file):
            with open(last_send_file, 'r') as f:
                last_send_time = f.read().strip()
                last_send_datetime = datetime.fromisoformat(last_send_time)
                time_diff = (datetime.now() - last_send_datetime).total_seconds()
                
                if time_diff < 120:  # Less than 2 minutes ago
                    logger.warning(f"Skipping duplicate send - last message sent {time_diff:.0f} seconds ago")
                    return 0, len(GROUP_IDS)
    except Exception as e:
        logger.debug(f"Could not check last send time: {e}")
    
    for chat_id in GROUP_IDS:
        if send_message(chat_id, MESSAGE):
            successful_sends += 1
        # Small delay between messages to avoid rate limiting
        time.sleep(1)
    
    # Record the send time to prevent duplicates
    try:
        with open(last_send_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.debug(f"Could not save last send time: {e}")
    
    logger.info(f"Broadcast completed: {successful_sends}/{len(GROUP_IDS)} messages sent successfully")
    return successful_sends, len(GROUP_IDS)


def setup_schedule():
    """
    Set up the message scheduling for specific times.
    """
    logger.info("Setting up message schedule...")
    
    # Clear existing schedule to avoid duplicates
    schedule.clear()
    
    for schedule_time in SCHEDULE_TIMES:
        # Convert GMT+3 time to UTC for scheduling
        utc_time = convert_to_utc_time(schedule_time)
        schedule.every().day.at(utc_time).do(send_to_all_groups)
        logger.info(f"Scheduled daily message broadcast at {schedule_time} (UTC: {utc_time})")
    
    logger.info(f"Total scheduled times: {len(SCHEDULE_TIMES)}")


def convert_to_utc_time(gmt_plus3_time):
    """
    Convert GMT+3 time to UTC time for scheduling.
    
    Args:
        gmt_plus3_time (str): Time in HH:MM format (GMT+3)
        
    Returns:
        str: Time in HH:MM format (UTC)
    """
    try:
        # Parse the time
        hour, minute = map(int, gmt_plus3_time.split(':'))
        
        # Convert from GMT+3 to UTC (subtract 3 hours)
        utc_hour = hour - 3
        
        # Handle day wraparound
        if utc_hour < 0:
            utc_hour += 24
        
        return f"{utc_hour:02d}:{minute:02d}"
    except:
        logger.error(f"Failed to convert time {gmt_plus3_time}")
        return gmt_plus3_time


def get_next_scheduled_time():
    """
    Get the next scheduled message time.
    
    Returns:
        str: Formatted next scheduled time
    """
    try:
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return "No upcoming schedule"
    except:
        return "Schedule not available"


def run_pending_jobs():
    """
    Check and run any pending scheduled jobs.
    """
    schedule.run_pending()


def save_schedule_config():
    """
    Save current schedule configuration to file.
    """
    config = {
        "schedule_times": SCHEDULE_TIMES,
        "timezone": TIMEZONE,
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        with open(SCHEDULE_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Schedule configuration saved to {SCHEDULE_CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save schedule config: {str(e)}")


def load_schedule_config():
    """
    Load schedule configuration from file if it exists.
    
    Returns:
        bool: True if config was loaded successfully, False otherwise
    """
    global SCHEDULE_TIMES, TIMEZONE
    
    try:
        if os.path.exists(SCHEDULE_CONFIG_FILE):
            with open(SCHEDULE_CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            SCHEDULE_TIMES = config.get("schedule_times", SCHEDULE_TIMES)
            TIMEZONE = config.get("timezone", TIMEZONE)
            
            logger.info(f"Schedule configuration loaded from {SCHEDULE_CONFIG_FILE}")
            return True
    except Exception as e:
        logger.error(f"Failed to load schedule config: {str(e)}")
    
    return False


def add_schedule_time(time_str):
    """
    Add a new scheduled time.
    
    Args:
        time_str (str): Time in HH:MM format
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        # Validate time format
        datetime.strptime(time_str, '%H:%M')
        
        if time_str not in SCHEDULE_TIMES:
            SCHEDULE_TIMES.append(time_str)
            SCHEDULE_TIMES.sort()
            
            # Add to schedule
            schedule.every().day.at(time_str).do(send_to_all_groups)
            
            logger.info(f"Added new scheduled time: {time_str}")
            save_schedule_config()
            return True
        else:
            logger.warning(f"Time {time_str} already exists in schedule")
            return False
            
    except ValueError:
        logger.error(f"Invalid time format: {time_str}. Use HH:MM format")
        return False


def remove_schedule_time(time_str):
    """
    Remove a scheduled time.
    
    Args:
        time_str (str): Time in HH:MM format
        
    Returns:
        bool: True if removed successfully, False otherwise
    """
    if time_str in SCHEDULE_TIMES:
        SCHEDULE_TIMES.remove(time_str)
        
        # Clear and recreate schedule
        schedule.clear()
        setup_schedule()
        
        logger.info(f"Removed scheduled time: {time_str}")
        save_schedule_config()
        return True
    else:
        logger.warning(f"Time {time_str} not found in schedule")
        return False


def list_scheduled_times():
    """
    Get a formatted list of all scheduled times.
    
    Returns:
        str: Formatted schedule information
    """
    if not SCHEDULE_TIMES:
        return "No scheduled times configured"
    
    schedule_info = f"Scheduled message times ({len(SCHEDULE_TIMES)} total):\n"
    for i, time_str in enumerate(SCHEDULE_TIMES, 1):
        schedule_info += f"  {i}. {time_str}\n"
    
    next_time = get_next_scheduled_time()
    schedule_info += f"Next broadcast: {next_time}"
    
    return schedule_info


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


def handle_command_line_args():
    """
    Handle command line arguments for schedule management.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Telegram Bot Schedule Manager')
    parser.add_argument('--add-time', type=str, help='Add a new scheduled time (HH:MM)')
    parser.add_argument('--remove-time', type=str, help='Remove a scheduled time (HH:MM)')
    parser.add_argument('--list-schedule', action='store_true', help='List current schedule')
    parser.add_argument('--test-send', action='store_true', help='Send test message immediately')
    
    args = parser.parse_args()
    
    # Load existing configuration
    load_schedule_config()
    
    if args.add_time:
        if add_schedule_time(args.add_time):
            print(f"Successfully added {args.add_time} to schedule")
        else:
            print(f"Failed to add {args.add_time} to schedule")
        sys.exit(0)
    
    elif args.remove_time:
        if remove_schedule_time(args.remove_time):
            print(f"Successfully removed {args.remove_time} from schedule")
        else:
            print(f"Failed to remove {args.remove_time} from schedule")
        sys.exit(0)
    
    elif args.list_schedule:
        print(list_scheduled_times())
        sys.exit(0)
    
    elif args.test_send:
        if validate_bot_token():
            print("Sending test message...")
            successful, total = send_to_all_groups()
            print(f"Test completed: {successful}/{total} messages sent successfully")
        else:
            print("Bot token validation failed")
        sys.exit(0)


def check_if_already_running():
    """
    Check if another instance of the bot is already running.
    
    Returns:
        bool: True if another instance is running, False otherwise
    """
    pid_file = 'telegram_bot.pid'
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process is still running
            try:
                os.kill(old_pid, 0)  # This doesn't kill, just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                os.remove(pid_file)
                return False
        except (ValueError, FileNotFoundError):
            # Invalid PID file, remove it
            try:
                os.remove(pid_file)
            except:
                pass
            return False
    
    return False


def create_pid_file():
    """
    Create a PID file to track the running process.
    """
    pid_file = 'telegram_bot.pid'
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logger.warning(f"Could not create PID file: {e}")


def remove_pid_file():
    """
    Remove the PID file when the bot stops.
    """
    pid_file = 'telegram_bot.pid'
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception as e:
        logger.debug(f"Could not remove PID file: {e}")


def main():
    """
    Main function to run the bot with advanced scheduled messaging.
    """
    # Handle command line arguments first
    if len(sys.argv) > 1:
        handle_command_line_args()
    
    # Check if another instance is already running
    if check_if_already_running():
        logger.error("Another instance of the bot is already running. Exiting.")
        sys.exit(1)
    
    # Create PID file to track this instance
    create_pid_file()
    
    logger.info("=" * 50)
    logger.info("Telegram Promotional Bot Starting")
    logger.info("=" * 50)
    
    # Start health check server for deployment monitoring
    health_server = start_health_check_server()
    if not health_server:
        logger.warning("Health check server failed to start, continuing without it...")
    
    # Load schedule configuration if available
    load_schedule_config()
    
    # Validate bot token before starting
    if not validate_bot_token():
        logger.error("Bot token validation failed. Please check your BOT_TOKEN environment variable.")
        sys.exit(1)
    
    # Set up the message schedule
    setup_schedule()
    
    # Save current configuration
    save_schedule_config()
    
    logger.info(f"Bot will send messages to {len(GROUP_IDS)} groups at scheduled times:")
    for schedule_time in SCHEDULE_TIMES:
        logger.info(f"  - Daily at {schedule_time}")
    
    # Show next scheduled time
    next_time = get_next_scheduled_time()
    logger.info(f"Next scheduled broadcast: {next_time}")
    logger.info(f"Timezone: {TIMEZONE}")
    
    # Main scheduling loop
    try:
        logger.info("Bot is now running. Use Ctrl+C to stop.")
        logger.info("Schedule management commands:")
        logger.info("  python telegram_bot.py --list-schedule")
        logger.info("  python telegram_bot.py --add-time HH:MM")
        logger.info("  python telegram_bot.py --remove-time HH:MM")
        logger.info("  python telegram_bot.py --test-send")
        
        # Counter to track consecutive errors
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # Check for pending scheduled jobs
                run_pending_jobs()
                
                # Reset error counter on successful run
                consecutive_errors = 0
                
                # Log heartbeat every 30 minutes to show bot is alive
                current_minute = datetime.now().minute
                if current_minute % 30 == 0:
                    next_scheduled = get_next_scheduled_time()
                    logger.info(f"Bot heartbeat - Next scheduled: {next_scheduled}")
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in scheduling loop (attempt {consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                
                # If too many consecutive errors, exit
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors. Exiting.")
                    break
                
                # Wait before retrying
                time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
        logger.info("Final schedule configuration saved")
        save_schedule_config()
        remove_pid_file()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
        save_schedule_config()
        remove_pid_file()
        sys.exit(1)
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
