#!/usr/bin/env python3
"""
Ultra-reliable keepalive message sender
Designed to work even when main processes fail
"""

import time
import requests
import os
import json
from datetime import datetime, timedelta
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
import sys

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093207171:AAGoIRsBcpBXPfLRz4RvXv3wMwdmEib6jn4')
GROUP_IDS = [-1002111810768, -1002098871252, -1001927958845, -1001508552538, -1001988059903]
SCHEDULE_TIMES = ["09:00", "14:45", "17:00", "21:00"]
LAST_SEND_FILE = "keepalive_last_send.json"
PORT = 5001

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

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        current_time = datetime.utcnow() + timedelta(hours=3)
        
        response = {
            "status": "alive",
            "service": "keepalive-sender",
            "current_time_gmt3": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "schedule": SCHEDULE_TIMES,
            "last_check": current_time.isoformat()
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        pass

def log(message):
    """Simple logging"""
    timestamp = datetime.utcnow() + timedelta(hours=3)
    print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    
    # Also write to file
    try:
        with open("keepalive.log", "a") as f:
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        pass

def send_message(chat_id, text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            log(f"Message sent to {chat_id}")
            return True
        else:
            log(f"Failed to send to {chat_id}: {result.get('description', 'Unknown')}")
            return False
    except Exception as e:
        log(f"Error sending to {chat_id}: {str(e)}")
        return False

def send_to_all():
    """Send to all groups"""
    log("Starting keepalive broadcast")
    success_count = 0
    
    for chat_id in GROUP_IDS:
        if send_message(chat_id, MESSAGE):
            success_count += 1
        time.sleep(1)
    
    log(f"Keepalive broadcast completed: {success_count}/{len(GROUP_IDS)}")
    return success_count

def get_current_time_gmt3():
    """Get current time in GMT+3"""
    return datetime.utcnow() + timedelta(hours=3)

def should_send():
    """Check if we should send now"""
    current_time = get_current_time_gmt3()
    current_time_str = current_time.strftime("%H:%M")
    
    if current_time_str not in SCHEDULE_TIMES:
        return False
    
    # Check if already sent recently
    try:
        if os.path.exists(LAST_SEND_FILE):
            with open(LAST_SEND_FILE, 'r') as f:
                data = json.load(f)
            
            last_send = datetime.fromisoformat(data['timestamp'])
            last_schedule = data['schedule_time']
            
            # Don't send if we sent within 10 minutes at same schedule time
            if (current_time - last_send).total_seconds() < 600 and last_schedule == current_time_str:
                return False
    except:
        pass
    
    return True

def record_send():
    """Record that we sent"""
    current_time = get_current_time_gmt3()
    data = {
        'timestamp': current_time.isoformat(),
        'schedule_time': current_time.strftime("%H:%M")
    }
    
    try:
        with open(LAST_SEND_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def start_http_server():
    """Start HTTP server in background"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), KeepAliveHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        log(f"HTTP server started on port {PORT}")
        
        # Test the server
        time.sleep(1)
        test_response = requests.get(f"http://localhost:{PORT}", timeout=5)
        if test_response.status_code == 200:
            log("HTTP server test successful")
        return server
    except Exception as e:
        log(f"Failed to start HTTP server: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    log("Received shutdown signal")
    sys.exit(0)

def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log("Keepalive sender started")
    
    # Start HTTP server
    server = start_http_server()
    
    # Main loop
    while True:
        try:
            current_time = get_current_time_gmt3()
            
            # Log every 30 minutes
            if current_time.minute % 30 == 0:
                log(f"Keepalive heartbeat - {current_time.strftime('%H:%M')} GMT+3")
            
            if should_send():
                log(f"Time {current_time.strftime('%H:%M')} matches schedule")
                success_count = send_to_all()
                
                if success_count > 0:
                    record_send()
                    log(f"Successfully sent {success_count} messages")
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()