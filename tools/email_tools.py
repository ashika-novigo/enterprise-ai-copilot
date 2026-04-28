# tools/email_tools.py
from langchain.tools import tool
import httpx
import os
 
POWER_AUTOMATE_URL = os.getenv('POWER_AUTOMATE_WEBHOOK_URL')
 
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send email via Power Automate HTTP trigger."""
    if not POWER_AUTOMATE_URL:
        return 'Email service not configured. Set POWER_AUTOMATE_WEBHOOK_URL in .env'
    try:
        payload  = {'to': to, 'subject': subject, 'body': body}
        response = httpx.post(POWER_AUTOMATE_URL, json=payload, timeout=10.0)
        if response.status_code in [200, 202]:
            return f'Email sent successfully to {to}'
        return f'Email failed: HTTP {response.status_code}'
    except Exception as e:
        return f'Email error: {str(e)}'
