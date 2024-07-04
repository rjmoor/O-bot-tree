import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY_2')
ACCOUNT_ID = os.getenv('ACCOUNT_ID_DEMO')
OANDA_URL = os.getenv('OANDA_URL_DEMO')

SECURE_HEADER = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}
