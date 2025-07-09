# Telegram Promotional Bot

## Overview

This is a Python-based Telegram promotional bot that automatically sends promotional messages to specified Telegram groups on a scheduled basis. The bot is designed to promote various community-related Telegram channels and groups, specifically targeting Ukrainian communities around Sofia area.

## System Architecture

### Core Architecture
- **Language**: Python 3
- **Runtime**: Script-based application with continuous execution
- **Scheduling**: Time-based scheduling using the `schedule` library
- **Communication**: HTTP-based API calls to Telegram Bot API
- **Data Persistence**: File-based storage for timestamps and configuration

### Key Design Decisions
- **Stateless Design**: The bot maintains minimal state, storing only the last send time and schedule configuration
- **Error Resilience**: Comprehensive error handling for network issues and API failures
- **Rate Limiting**: Built-in delays between messages to comply with Telegram's rate limits
- **Configuration Management**: JSON-based configuration for flexible scheduling
- **Health Check Integration**: HTTP endpoint for deployment monitoring and health status
- **Dual Operation Mode**: Scheduled messaging with concurrent health check server

## Key Components

### 1. Main Bot Script (`telegram_bot.py`)
- **Purpose**: Core bot logic and message sending functionality
- **Responsibilities**:
  - Telegram Bot API communication
  - Message scheduling and delivery
  - Error handling and logging
  - Rate limiting between group messages

### 2. Schedule Configuration (`schedule_config.json`)
- **Purpose**: Stores scheduled send times and timezone information
- **Current Schedule**: 5 times daily at 09:00, 13:00, 15:30, 17:00, and 21:00 (GMT+3)
- **Flexibility**: Easily configurable for different time zones and schedules

### 3. Last Send Time Tracking (`last_send_time.txt`)
- **Purpose**: Prevents duplicate sends and maintains execution state
- **Format**: ISO timestamp format for precise time tracking

### 4. Logging System
- **Dual Output**: Both file (`telegram_bot.log`) and console logging
- **Level**: INFO level for operational visibility
- **Format**: Timestamped entries with log levels

## Data Flow

1. **Initialization**: Bot validates token and loads configuration
2. **Schedule Check**: Continuous monitoring of scheduled send times
3. **Message Dispatch**: Sequential sending to all target groups with rate limiting
4. **State Update**: Recording of last send time and schedule updates
5. **Error Handling**: Graceful handling of network or API failures with retry logic

## External Dependencies

### Required Python Packages
- `requests`: HTTP client for Telegram Bot API calls
- `schedule`: Task scheduling library
- Standard library modules: `time`, `os`, `logging`, `datetime`, `json`

### External Services
- **Telegram Bot API**: Primary communication channel
- **Telegram Groups**: Target destinations for promotional messages

### Environment Variables
- `BOT_TOKEN`: Telegram bot authentication token (with fallback to hardcoded value)

## Deployment Strategy

### Current Setup
- **Execution Model**: Continuous running script (background worker)
- **Environment**: Replit with Python 3.11 environment
- **Dependencies**: `requests` and `schedule` packages
- **Configuration**: Environment variables (BOT_TOKEN) and JSON files
- **Deployment Type**: GCE background worker with ignorePorts=true

### Deployment Configuration
- **File**: `replit.toml` with GCE deployment configuration
- **Type**: GCE deployment with HTTP health check endpoint
- **Port**: 5000 (health check endpoint for deployment monitoring)
- **Endpoints**: `/health` and `/` for status monitoring
- **Secrets**: BOT_TOKEN environment variable for Telegram API authentication
- **Monitoring**: Built-in logging and HTTP health check endpoint

## Changelog

```
Changelog:
- July 07, 2025. Initial setup
- July 07, 2025. Fixed deployment configuration:
  * Created replit.toml with background worker configuration
  * Added BOT_TOKEN secret for proper authentication
  * Updated deployment type to GCE with ignorePorts=true
  * Bot now successfully validates and runs with scheduled messaging
- July 07, 2025. Fixed GCE deployment issue:
  * Added HTTP health check endpoint on port 5000
  * Removed conflicting background-worker type specification
  * Changed ignorePorts from true to false for proper health checks
  * Bot now exposes /health endpoint for deployment monitoring
  * Successfully resolves "No open port detected" deployment error
- July 08, 2025. Enhanced bot stability and monitoring:
  * Fixed duplicate message sending issue
  * Added error recovery mechanism with retry logic
  * Implemented heartbeat logging every 30 minutes
  * Created restart_bot.sh script for automatic recovery
  * Added consecutive error tracking to prevent infinite loops
- July 09, 2025. Fixed timezone and scheduling issues:
  * Corrected timezone from GMT+2 to GMT+3
  * Updated schedule: 09:00, 14:45, 17:00, 21:00 (removed 13:00 and 15:30)
  * Added proper UTC conversion for scheduling (GMT+3 to UTC)
  * Fixed missed message sending due to timezone misconfiguration
- July 09, 2025. Implemented dual reliability system:
  * Created independent cron_sender.py as backup mechanism
  * Added second workflow "Cron Sender" for redundancy
  * Both systems check time independently and prevent duplicates
  * Ensures message delivery even if main bot crashes
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## Technical Notes

### Target Groups
The bot currently targets 4 specific Telegram groups with promotional content about Ukrainian community channels in the Sofia area, including:
- Real estate channels
- Auto sales groups
- News channels
- Community chats
- Job boards
- Residential complex chats

### Rate Limiting
The bot implements delays between messages to comply with Telegram's API rate limits and avoid being flagged as spam.

### Error Handling
Comprehensive error handling covers:
- Network connectivity issues
- Telegram API errors
- Invalid bot tokens
- Group access permissions
- Rate limiting responses