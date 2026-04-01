from collections.abc import Callable
from typing import Any, TypeAlias

from eth_account.messages import encode_defunct
from loguru import logger
from web3 import Web3

from app.domain.models import AccountProcessingResult, ResultFile
from app.layer.debankType import ConfigStruct
from app.utils.captcha_solver import solve_captcha
from app.utils.exceptions import ApiProtocolError, ApiResponseError
from app.utils.retry import retry_call

from .debankParser import do_request

Proxy: TypeAlias = dict[str, str] | None
WalletAccount: TypeAlias = dict[str, Any]
WalletAccountData: TypeAlias = tuple[WalletAccount, Proxy]
CaptchaSolverFunc: TypeAlias = Callable[[str, str], str]


def get_sign_l2(account_address: str, proxy: Proxy) -> str:
    base_url = "https://api.debank.com/user/sign_v2"
    path = "/user/sign_v2"
    payload = {
        "id": account_address.lower(),
        "chain_id": "1",
    }

    response = do_request(account_address, base_url, "POST", path, {}, payload, proxy)
    if response.get("error_code") != 0:
        raise ApiResponseError(f"{account_address} | Failed to fetch Debank sign text")

    try:
        return response["data"]["text"]
    except KeyError as exc:
        raise ApiProtocolError(
            f"{account_address} | Debank sign response is missing text"
        ) from exc


def sign_message(message_text: str, private_key_hex: str) -> str:
    web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))
    validate_msg = encode_defunct(text=message_text)
    signature = web3.eth.account.sign_message(validate_msg, private_key=private_key_hex)
    return signature.signature.hex()


def do_auth(
    account_address: str,
    captcha_response: str,
    signed_message: str,
    proxy: Proxy,
) -> str:
    base_url = "https://api.debank.com/user/login_v2"
    path = "/user/login_v2"
    payload = {
        "token": captcha_response,
        "id": account_address.lower(),
        "chain_id": "1",
        "signature": signed_message,
    }

    response = do_request(account_address, base_url, "POST", path, {}, payload, proxy)
    if response.get("error_code") != 0:
        raise ApiResponseError(f"{account_address} | Debank login failed")

    try:
        return response["data"]["session_id"]
    except KeyError as exc:
        raise ApiProtocolError(
            f"{account_address} | Debank login response is missing session_id"
        ) from exc


def get_l2_balance(account_address: str, session_id: str, proxy: Proxy) -> float:
    base_url = "https://api.debank.com/user/l2_account"
    path = "/user/l2_account"
    payload = {"id": account_address.lower()}
    params = {"id": account_address.lower()}

    response = do_request(
        account_address,
        base_url,
        "GET",
        path,
        params,
        payload,
        proxy,
        session_id,
    )
    if response.get("error_code") != 0:
        raise ApiResponseError(f"{account_address} | Failed to fetch Debank L2 balance")

    try:
        return float(response["data"]["balance"])
    except KeyError as exc:
        raise ApiProtocolError(
            f"{account_address} | Debank L2 response is missing balance"
        ) from exc


def debank_l2_balance_parser(
    account_data: WalletAccountData,
    config: ConfigStruct,
    captcha_solver: CaptchaSolverFunc = solve_captcha,
) -> AccountProcessingResult:
    account, proxy = account_data
    account_address = str(account["wallet"].address)
    private_key = account["wallet"].privateKey

    message_text = retry_call(
        lambda: get_sign_l2(account_address, proxy),
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} fetch Debank sign text",
    )
    message_signed = sign_message(message_text, private_key.hex())
    captcha_response = captcha_solver(account_address, config.two_captcha_apikey)
    session_id = retry_call(
        lambda: do_auth(account_address, captcha_response, message_signed, proxy),
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} Debank login",
    )
    account_balance = retry_call(
        lambda: get_l2_balance(account_address, session_id, proxy),
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} fetch Debank L2 balance",
    )

    logger.info("{} | L2 balance: {} $", account_address, account_balance)

    files: list[ResultFile] = []
    if account_balance > 0:
        files.append(
            ResultFile(
                file_name="debank_l2_balances.txt",
                content=f"{account_address} | {account_balance} $\n",
            )
        )

    return AccountProcessingResult(
        account_address=account_address,
        total_balance=float(account_balance),
        files=files,
    )
