import requests
from loguru import logger

from app.utils.exceptions import CaptchaError, RetryableOperationError
from app.utils.retry import retry_call


def create_task(account_address: str, api_key: str) -> str:
    payload = {
        "clientKey": api_key,
        "softId": 4759,
        "task": {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": "https://debank.com/",
            "websiteKey": "6Lcw7ewpAAAAAPtZi4LTNCAWmWj-1h5ACTD_CQHE",
            "minScore": 0.9,
        },
    }

    response = requests.post(
        "https://api.2captcha.com/createTask",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    try:
        response_data = response.json()
    except ValueError as exc:
        raise CaptchaError(
            f"{account_address} | Failed to parse createTask response"
        ) from exc

    if response_data.get("errorId") != 0:
        raise CaptchaError(
            f"{account_address} | 2captcha createTask error: {response_data}"
        )

    task_id = response_data.get("taskId")
    if not task_id:
        raise CaptchaError(
            f"{account_address} | 2captcha createTask returned no taskId"
        )

    logger.info("{} | Captcha task created: {}", account_address, task_id)
    return str(task_id)


def get_task_result(account_address: str, task_id: str, api_key: str) -> str:
    payload = {
        "softId": 4759,
        "clientKey": api_key,
        "taskId": task_id,
    }

    response = requests.post(
        "https://api.2captcha.com/getTaskResult",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    try:
        response_data = response.json()
    except ValueError as exc:
        raise CaptchaError(
            f"{account_address} | Failed to parse getTaskResult response"
        ) from exc

    if response_data.get("errorId") != 0:
        raise CaptchaError(
            f"{account_address} | 2captcha getTaskResult error: {response_data}"
        )

    status = response_data.get("status")
    if status == "ready":
        solution = response_data.get("solution", {})
        token = solution.get("token")
        if not token:
            raise CaptchaError(
                f"{account_address} | 2captcha returned ready status without token"
            )
        return token

    if status == "processing":
        raise RetryableOperationError(f"{account_address} | Captcha is still processing")

    raise CaptchaError(
        f"{account_address} | Unexpected captcha status: {response_data}"
    )


def solve_captcha(account_address: str, api_key: str) -> str:
    task_id = retry_call(
        lambda: create_task(account_address, api_key),
        attempts=5,
        initial_delay=2.0,
        backoff=1.5,
        operation_name=f"{account_address} create captcha task",
        retry_exceptions=(requests.RequestException, CaptchaError),
    )

    return retry_call(
        lambda: get_task_result(account_address, task_id, api_key),
        attempts=24,
        initial_delay=5.0,
        backoff=1.0,
        operation_name=f"{account_address} resolve captcha",
        retry_exceptions=(
            requests.RequestException,
            CaptchaError,
            RetryableOperationError,
        ),
    )

