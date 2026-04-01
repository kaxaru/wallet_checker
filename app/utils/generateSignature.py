import hashlib
import hmac
import random
import time
import uuid
from urllib.parse import parse_qs, urlencode

from app.layer.debankType import RequestParamsStruct


def generate_random_id_with_ts() -> tuple[str, int]:
    random_uuid = uuid.uuid4()
    return "".join(str(random_uuid).split("-")), _get_timestamp()


def sort_query_string(query_string: str) -> str:
    params = parse_qs(query_string)
    sorted_keys = sorted(params.keys())
    sorted_params = [f"{key}={params[key][0]}" for key in sorted_keys]
    return "&".join(sorted_params)


def custom_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def generate_nonce(length: int = 40) -> str:
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"
    nonce = "".join(
        charset[int(random.random() * len(charset))]
        for _ in range(length)
    )
    return f"n_{nonce}"


def _get_timestamp() -> int:
    return int(time.time())


def hmac_sha256(key: bytes, data: bytes) -> str:
    hmac_obj = hmac.new(key, data, hashlib.sha256)
    return hmac_obj.hexdigest()


def map_to_query_string(payload: dict[str, str | int | float]) -> str:
    return urlencode({key: str(value) for key, value in payload.items()})


def generate_signature(
    payload: dict[str, str | int | float],
    method: str,
    path: str,
) -> RequestParamsStruct:
    try:
        nonce = generate_nonce(40)
        api_ts = _get_timestamp()
    except Exception as exc:
        raise RuntimeError(f"Failed to generate nonce: {exc}") from exc

    query_string = map_to_query_string(payload)

    key = f"debank-api\n{nonce}\n{api_ts}"
    sorted_params = sort_query_string(query_string)
    sign_data = f"{method.upper()}\n{path.lower()}\n{sorted_params.lower()}"

    rand_str_hash = custom_sha256(key)
    request_params_hash = custom_sha256(sign_data)
    signature = hmac_sha256(rand_str_hash.encode(), request_params_hash.encode())

    return RequestParamsStruct(
        **{
            "nonce": nonce,
            "signature": signature,
            "timestamp": str(api_ts),
        }
    )
