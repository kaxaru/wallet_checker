import uuid
import time
from layer.debankType import RequestParamsStruct, Info


def _get_timestamp() -> int:
    return int(time.time())

def generate_random_id_with_ts() -> str:
    rnd_uuid = uuid.uuid4()
    return ''.join(rnd_uuid.__str__().split('-')), _get_timestamp()


def generate_account() -> str:
    rnd_id, rnd_ts = generate_random_id_with_ts()

    info = Info(**{
        "random_at": rnd_ts,
        "random_id": rnd_id,
        "user_addr": None,
        "connected_addr": None
    })

    try:
        account_header = info.json()
    except Exception as e:
        raise RuntimeError(f"Failed to generate account header: {e}")


    return account_header
