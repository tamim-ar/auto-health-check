import json
import logging
import requests
import time
import smtplib
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from discord_webhook import DiscordWebhook
from email.mime.text import MIMEText

# Setup logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "health_check.log")
logger = logging.getLogger("HealthCheck")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Add service state tracking at the top level
service_states = {}

# Add notification cooldown tracking
notification_cooldowns = {}
NOTIFICATION_COOLDOWN = 300  # 5 minutes in seconds

def can_send_notification(service_name):
    global notification_cooldowns
    now = datetime.now()
    if service_name in notification_cooldowns:
        last_notification = notification_cooldowns[service_name]
        if now - last_notification < timedelta(seconds=NOTIFICATION_COOLDOWN):
            return False
    notification_cooldowns[service_name] = now
    return True

def load_services_from_txt(filepath):
    services = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    category, name, url, status = line.strip().split('|')
                    services.append({
                        'category': category,
                        'name': name,
                        'url': url,
                        'expected_status': int(status)
                    })
        return services
    except Exception as e:
        logger.error(f"Failed to load services from {filepath}: {str(e)}")
        return []

def load_config():
    config = {}
    # Load main configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Try to load services from txt file if it exists
    txt_services = load_services_from_txt('services.txt')
    if txt_services:
        config['services'] = txt_services
    
    return config

def format_error_message(error, service):
    category = service.get('category', 'Unknown')
    if isinstance(error, requests.exceptions.ConnectionError):
        if "Connection refused" in str(error) or "10061" in str(error):
            if category == 'Local':
                return "🔴 Service is not running locally"
            return "🔴 Connection refused by remote host"
        return "🟡 Connection failed - Service may be temporarily unavailable"
    return str(error)

def send_discord_alert(webhook_url, service, error_message, is_recovery=False):
    if not webhook_url or not webhook_url.startswith(('http://', 'https://')):
        logger.error("Invalid Discord webhook URL. Skipping Discord notification.")
        return
        
    try:
        category = service.get('category', 'Unknown')
        status_emoji = "✅" if is_recovery else "⚠️"
        status_text = "Recovered" if is_recovery else "Down"
        
        # Define embed color based on status and category
        if is_recovery:
            color = 0x00FF00  # Green
        elif category == 'Local':
            color = 0xFF0000  # Red
        else:
            color = 0xFFA500  # Orange

        embed = {
            "title": f"{status_emoji} Service Status Alert",
            "description": f"**Service:** {service['name']}\n**Category:** {category}",
            "color": color,
            "fields": [
                {
                    "name": "Status",
                    "value": status_text,
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        if error_message and not is_recovery:
            embed["fields"].append({
                "name": "Error Details",
                "value": error_message,
                "inline": False
            })

        webhook = DiscordWebhook(url=webhook_url, embeds=[embed])
        webhook.execute()
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {str(e)}")

def send_email_alert(config, service_name, error_message):
    try:
        msg = MIMEText(f"Service {service_name} is down!\nError: {error_message}")
        msg['Subject'] = f"Service Alert: {service_name}"
        msg['From'] = config['notifications']['email']['sender_email']
        msg['To'] = config['notifications']['email']['recipient_email']

        with smtplib.SMTP(config['notifications']['email']['smtp_server'], 
                          config['notifications']['email']['smtp_port']) as server:
            server.starttls()
            server.login(
                config['notifications']['email']['sender_email'],
                config['notifications']['email']['sender_password']
            )
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")

def check_service(service, config):
    global service_states
    service_name = service['name']
    try:
        response = requests.get(service['url'], timeout=5)
        if response.status_code != service['expected_status']:
            error_msg = f"Unexpected status code: {response.status_code}"
            logger.error(f"Service {service_name} check failed: {error_msg}")
            service_states[service_name] = False
            send_alerts(service, error_msg, config)
        else:
            logger.info(f"Service {service_name} is healthy")
            if service_name in service_states and not service_states[service_name]:
                service_states[service_name] = True
                send_alerts(service, "", config, is_recovery=True)
            service_states[service_name] = True
    except requests.RequestException as e:
        error_msg = format_error_message(e, service)
        logger.error(f"Service {service_name} check failed: {error_msg}")
        service_states[service_name] = False
        send_alerts(service, error_msg, config)

def send_alerts(service, error_message, config, is_recovery=False):
    service_name = service['name']
    if not is_recovery and not can_send_notification(service_name):
        logger.info(f"Skipping notification for {service_name} due to cooldown")
        return

    if config['notifications']['discord']['enabled']:
        send_discord_alert(
            config['notifications']['discord']['webhook_url'],
            service,
            error_message,
            is_recovery
        )
    
    if config['notifications']['email']['enabled'] and not is_recovery:
        send_email_alert(config, service_name, error_message)

def main():
    logger.info("Starting health check service")
    config = load_config()
    
    while True:
        for service in config['services']:
            check_service(service, config)
        time.sleep(config['check_interval'])

if __name__ == "__main__":
    main()
