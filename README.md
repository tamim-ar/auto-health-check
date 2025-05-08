# Auto Health Check

## Quick Start

1. Install all dependencies:
```bash
pip install -r requirements.txt
npm install
```

2. Run everything with one command:
```bash
python start.py
```

This will start:
- Flask test app on port 5000
- Node.js test app on port 3000
- Health checker monitoring both services

Press Ctrl+C to stop all services.

## Features

- Monitor multiple HTTP/HTTPS services
- Discord webhook notifications with embedded messages
- Email notifications support (Gmail and other SMTP)
- Service categorization (Local/External)
- Automatic recovery detection
- Rate-limited notifications (5 min cooldown)
- Log rotation and management

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure services in `services.txt`:
```
Category|Service Name|URL|Expected Status
Local|Local Flask App|http://localhost:5000|200
Local|Local Node App|http://localhost:3000|200
External|Sample API|https://api.example.com/health|200
```

3. Configure notifications in `config.json`:
```json
{
  "notifications": {
    "discord": {
      "enabled": true,
      "webhook_url": "your-discord-webhook-url"
    },
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "your-email@gmail.com",
      "sender_password": "your-app-password",
      "recipient_email": "alerts@yourdomain.com"
    }
  },
  "check_interval": 300
}
```

4. Run the service:
```bash
python health_check.py
```

## Docker Usage

Build and run with Docker:

```bash
# Build image
docker build -t auto-health-check .

# Run with mounted config and logs
docker run -d \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/services.txt:/app/services.txt \
  -v $(pwd)/logs:/app/logs \
  --name health-check \
  auto-health-check
```

## Service Configuration

Services can be defined in two ways:

1. In `services.txt` (recommended):
   - One service per line
   - Format: `Category|Name|URL|ExpectedStatus`
   - Lines starting with # are ignored
   - Categories: Local, External, etc.

2. In `config.json` under "services" section:
```json
{
  "services": [
    {
      "category": "Local",
      "name": "Service Name",
      "url": "http://localhost:port",
      "expected_status": 200
    }
  ]
}
```

## Notification Types

### Discord Notifications
- Rich embeds with service status
- Color-coded by category and status
- Recovery notifications
- Rate-limited to prevent spam
- Shows timestamp and error details

### Email Notifications
- Sent only for failures (not recovery)
- Contains service name and error details
- Supports custom SMTP configuration

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| check_interval | Time between checks (seconds) | 300 |
| notifications.discord.enabled | Enable Discord alerts | true |
| notifications.email.enabled | Enable email alerts | false |

## Logs

- Location: `logs/health_check.log`
- Rotation: 1MB file size
- Keeps last 5 log files
- Format: `timestamp - name - level - message`

## Requirements

- Python 3.9+
- Network access to monitored services
- Discord webhook URL (for Discord notifications)
- SMTP credentials (for email notifications)

## Testing MongoDB Monitoring

1. Install MongoDB locally or use Docker:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

2. Start the MongoDB test endpoint:
```bash
python test_mongodb.py
```

This will create a test endpoint that checks MongoDB connectivity.
