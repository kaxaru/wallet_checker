import uuid
from datetime import datetime


def generate_api_key() -> tuple[str, str]:
    debank_api_key = str(uuid.uuid4())
    debank_api_time = str(int(datetime.timestamp(datetime.now())))

    return debank_api_key, debank_api_time
