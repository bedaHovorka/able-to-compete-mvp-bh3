import logging
import sys
from datetime import datetime
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(settings.APP_NAME)


def log_activity(action: str, entity_type: str, entity_id: str, user_id: str = None, details: str = None):
    """Log user activity for audit trail"""
    logger.info(f"Activity: {action} | Entity: {entity_type}:{entity_id} | User: {user_id} | Details: {details}")
