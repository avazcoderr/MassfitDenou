import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
GROUP_ID = os.getenv('GROUP_ID')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
# Set to 'false' to disable subscription checking (for testing)
ENABLE_SUBSCRIPTION_CHECK = os.getenv('ENABLE_SUBSCRIPTION_CHECK', 'true').lower() == 'true'

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS
