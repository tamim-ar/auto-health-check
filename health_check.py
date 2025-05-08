import json
import logging
import requests
import time
import smtplib
import os
from datetime import datetime
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

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def send_discord_alert(webhook_url, service_name, error_message):
    webhook = DiscordWebhook(
        url=webhook_url,
        content=f"⚠️ Service Alert: {service_name} is down!\nError: {error_message}"
    )
    webhook.execute()

def send_email_alert(config, service_name, error_message):
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

def check_service(service, config):
    try:
        response = requests.get(service['url'], timeout=5)
        if response.status_code != service['expected_status']:
            error_msg = f"Unexpected status code: {response.status_code}"
            logger.error(f"Service {service['name']} check failed: {error_msg}")
            send_alerts(service['name'], error_msg, config)
        else:
            logger.info(f"Service {service['name']} is healthy")
    except requests.RequestException as e:
        error_msg = str(e)
        logger.error(f"Service {service['name']} check failed: {error_msg}")
        send_alerts(service['name'], error_msg, config)

def send_alerts(service_name, error_message, config):
    if config['notifications']['discord']['enabled']:
        send_discord_alert(
            config['notifications']['discord']['webhook_url'],
            service_name,
            error_message
        )
    
    if config['notifications']['email']['enabled']:
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
