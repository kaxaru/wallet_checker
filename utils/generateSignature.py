import hmac
import hashlib
import json
import random
import string
import time
from urllib.parse import urlencode, parse_qs, quote_plus
from typing import Dict, Tuple, Union

def generate_random_id() -> str:
    chars = "abcdef0123456789"
    return ''.join(random.choice(chars) for _ in range(32))


def sort_query_string(query_string: str) -> str:
    params = parse_qs(query_string)
    sorted_keys = sorted(params.keys())
    sorted_params = [f"{key}={params[key][0]}" for key in sorted_keys]
    return "&".join(sorted_params)


def custom_sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def generate_nonce(length: int) -> str:
    letters = string.ascii_letters + string.digits
    nonce = ''.join(random.choice(letters) for _ in range(length))
    return f"n_{nonce}"


def hmac_sha256(key: bytes, data: bytes) -> str:
    hmac_obj = hmac.new(key, data, hashlib.sha256)
    return hmac_obj.hexdigest()


# def map_to_query_string(payload: dict) -> str:
#     return urlencode(payload, quote_via=quote_plus)

def map_to_query_string(payload: Dict[str, Union[str, int, float]]) -> str:
    return urlencode({key: str(value) for key, value in payload.items()})


def generate_signature(payload: dict, method: str, path: str):
    try:
        nonce = generate_nonce(40)
    except Exception as e:
        raise RuntimeError(f"Failed to generate nonce: {e}")

    query_string = map_to_query_string(payload)

    timestamp = int(time.time())
    rand_str = f"debank-api\n{nonce}\n{timestamp}"
    rand_str_hash = custom_sha256(rand_str)

    request_params = f"{method.upper()}\n{path.lower()}\n{sort_query_string(query_string.lower())}"
    request_params_hash = custom_sha256(request_params)

    info = {
        "random_at": timestamp,
        "random_id": generate_random_id(),
        "user_addr": None
    }

    try:
        account_header = json.dumps(info)
    except Exception as e:
        raise RuntimeError(f"Failed to generate account header: {e}")

    signature = hmac_sha256(rand_str_hash.encode(), request_params_hash.encode())

    result = {
        "AccountHeader": account_header,
        "Nonce": nonce,
        "Signature": signature,
        "Timestamp": str(timestamp),
    }

    return result