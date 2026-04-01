from typing import Any, TypeAlias
from urllib.parse import urlencode

import requests
from loguru import logger

from app.domain.models import AccountProcessingResult, ResultFile
from app.layer.debankType import RabbyReturnData
from app.utils.exceptions import ApiProtocolError, RateLimitError
from app.utils.result_sink import build_bucketed_result_file_name
from app.utils.retry import retry_call

Proxy: TypeAlias = dict[str, str] | None
AccountEntry: TypeAlias = str | dict[str, Any]
RawAccountData: TypeAlias = tuple[AccountEntry, Proxy]


def get_total_balance(
    account_address: str,
    proxy: Proxy,
) -> tuple[float, list[RabbyReturnData]]:
    base_url = "https://api.rabby.io/v1/user/total_balance"
    params = {"id": account_address}
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru,en;q=0.9",
    }

    def operation() -> tuple[float, list[RabbyReturnData]]:
        response = requests.get(
            f"{base_url}?{urlencode(params)}",
            headers=headers,
            proxies=proxy,
            timeout=15,
        )

        if response.status_code in {429, 403}:
            raise RateLimitError(f"{account_address} | Rate limited by Rabby")
        response.raise_for_status()

        try:
            response_data = response.json()
        except ValueError as exc:
            raise ApiProtocolError(
                f"{account_address} | Failed to parse Rabby response"
            ) from exc

        if response_data.get("message") == "Too Many Requests":
            raise RateLimitError(f"{account_address} | Rate limited by Rabby")

        total_usd_balance = float(response_data["total_usd_value"])
        chain_balances: list[RabbyReturnData] = []

        for current_chain in response_data["chain_list"]:
            if current_chain["usd_value"] <= 0:
                continue

            chain_balances.append(
                RabbyReturnData(
                    chain_name=current_chain["name"],
                    chain_balance=current_chain["usd_value"],
                )
            )

        return total_usd_balance, chain_balances

    return retry_call(
        operation,
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} Rabby total balance",
        retry_exceptions=(requests.RequestException, RateLimitError, ApiProtocolError),
    )


def parse_rabby_account(account_data: RawAccountData) -> AccountProcessingResult:
    account_address, proxy = account_data

    if isinstance(account_address, dict) and "wallet" in account_address:
        account_address = str(account_address["wallet"].address)

    total_usd_balance, chain_balances = get_total_balance(account_address, proxy)
    sorted_chain_balances = sorted(
        chain_balances,
        key=lambda chain: chain.chain_balance,
        reverse=True,
    )

    formatted_result = (
        f"Address: {account_address}\n"
        f"Total Balance: {total_usd_balance:.2f} $\n\n"
    )
    for chain in sorted_chain_balances:
        formatted_result += f"{chain.chain_name} | {chain.chain_balance:.2f} $\n"
    formatted_result += "\n\n"

    logger.info("{} | Total USD Balance: {:.2f} $", account_address, total_usd_balance)

    return AccountProcessingResult(
        account_address=account_address,
        total_balance=float(total_usd_balance),
        files=[
            ResultFile(
                file_name=build_bucketed_result_file_name("rabby", total_usd_balance),
                content=formatted_result,
            )
        ],
    )
