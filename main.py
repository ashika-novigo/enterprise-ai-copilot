import httpx, os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('POWER_AUTOMATE_WEBHOOK_URL')

payload = {
    "to": "ashika.shridhar@novigosolutions.com",
    "subject": "Test from Enterprise Copilot",
    "body": "Your leave request has been submitted."
}

headers = {
    "Content-Type": "application/json"
}

response = httpx.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.text)  # 👈 VERY IMPORTANT