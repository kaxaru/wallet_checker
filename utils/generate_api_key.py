import uuid
from datetime import datetime

def generate_api_key() -> str:
    DEBANK_API_KEY = uuid.uuid4()
    DEBANK_API_TIME = int(datetime.timestamp(datetime.now()))

    return DEBANK_API_KEY, DEBANK_API_TIME
