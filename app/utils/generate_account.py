import time
import uuid

from app.layer.debankType import Info


def _get_timestamp() -> int:
    return int(time.time())


def generate_random_id_with_ts() -> tuple[str, int]:
    random_uuid = uuid.uuid4()
    return "".join(str(random_uuid).split("-")), _get_timestamp()


def generate_account() -> str:
    random_id, random_ts = generate_random_id_with_ts()

    info = Info(
        **{
            "random_at": random_ts,
            "random_id": random_id,
            "user_addr": None,
            "connected_addr": None,
        }
    )

    try:
        account_header = info.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to generate account header: {exc}") from exc

    return account_header
