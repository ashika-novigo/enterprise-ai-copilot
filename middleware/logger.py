# middleware/logger.py
import logging, json
from datetime import datetime
import os
 
os.makedirs('logs', exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs\\copilot.log'),  # Windows path
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('copilot')
 
def log_interaction(employee_id, query, intent, agent, response_ms, success):
    entry = {
        'timestamp':   datetime.utcnow().isoformat(),
        'employee_id': employee_id,
        'query':       query[:200],
        'intent':      intent,
        'agent':       agent,
        'response_ms': response_ms,
        'success':     success,
    }
    logger.info(json.dumps(entry))
