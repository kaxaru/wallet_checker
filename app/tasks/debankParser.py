import json
import random
import time
from decimal import Decimal
from typing import Any, TypeAlias
from urllib.parse import urlencode

from curl_cffi import requests as curl_requests
from loguru import logger
from pyuseragents import random as random_useragent

from app.domain.models import AccountProcessingResult
from app.layer.debankType import (
    ConfigStruct,
    NftBalancesResultData,
    PoolBalancesResultData,
    RequestSessionStruct,
    TokenBalancesResultData,
)
from app.utils.debankResult import format_result
from app.utils.exceptions import (
    ApiProtocolError,
    ApiRequestError,
    ApiResponseError,
    RateLimitError,
    RetryableOperationError,
)
from app.utils.generateSignature import generate_signature
from app.utils.generate_account import generate_account
from app.utils.generate_api_key import generate_api_key
from app.utils.retry import retry_call

Proxy: TypeAlias = dict[str, str] | None
AccountEntry: TypeAlias = str | dict[str, Any]
RawAccountData: TypeAlias = tuple[AccountEntry, Proxy]
NormalizedAccountData: TypeAlias = tuple[str, Proxy]
RequestPayload: TypeAlias = dict[str, Any]
Headers: TypeAlias = dict[str, str]
ResponseData: TypeAlias = dict[str, Any]
TokenBalancesByChain: TypeAlias = dict[str, list[TokenBalancesResultData]]
NftBalancesByChain: TypeAlias = dict[str, list[NftBalancesResultData]]
PoolBalancesByChain: TypeAlias = dict[str, dict[str, list[PoolBalancesResultData]]]

DEBANK_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (
    ApiRequestError,
    ApiResponseError,
    RetryableOperationError,
)


def _build_account_header(account_address: str, session_id: str | None) -> str:
    try:
        account_header = generate_account()
        if session_id is None:
            return account_header

        account_payload = json.loads(account_header)
        account_payload["user_addr"] = account_address.lower()
        account_payload["session_id"] = session_id
        account_payload["wallet_type"] = "metamask"
        account_payload["is_verified"] = True

        return RequestSessionStruct(**account_payload).json()
    except Exception as exc:
        raise ApiRequestError(
            f"{account_address} | Failed to build account headers"
        ) from exc


def _build_headers(
    account_address: str,
    method: str,
    path: str,
    payload: RequestPayload,
    session_id: str | None,
) -> Headers:
    try:
        account_header = _build_account_header(account_address, session_id)

        if method == "POST":
            time.sleep(random.randint(2, 5))
            api_key, api_time = generate_api_key()
            time.sleep(random.randint(3, 5))
            request_params = generate_signature({}, method, path)
        else:
            time.sleep(random.randint(1, 2))
            api_key, api_time = generate_api_key()
            time.sleep(random.randint(1, 2))
            request_params = generate_signature(payload, method, path)
    except Exception as exc:
        raise ApiRequestError(
            f"{account_address} | Failed to generate request params"
        ) from exc

    headers: Headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,be;q=0.6,zh-CN;q=0.5,zh;q=0.4,uk;q=0.3",
        "origin": "https://debank.com",
        "referer": "https://debank.com/",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "source": "web",
        "x-api-ver": "v2",
        "account": account_header,
        "x-api-nonce": request_params.nonce,
        "x-api-sign": request_params.signature,
        "x-api-ts": request_params.timestamp,
        "x-api-key": api_key,
        "x-api-time": api_time,
        "user-agent": random_useragent(),
    }
    if method == "POST":
        headers["Content-Type"] = "application/json"

    return headers


def _send_request(
    method: str,
    url: str,
    headers: Headers,
    payload: RequestPayload | None,
    proxy: Proxy,
) -> Any:
    request_func = curl_requests.post if method == "POST" else curl_requests.get
    request_kwargs: dict[str, Any] = {
        "url": url,
        "headers": headers,
        "impersonate": "chrome120",
    }

    if method == "POST" and payload is not None:
        try:
            request_kwargs["data"] = json.dumps(payload)
        except Exception as exc:
            raise ApiRequestError(f"Failed to serialize request body for {url}") from exc

    proxy_url = proxy.get("http") if proxy else None
    if proxy_url:
        try:
            return request_func(proxy=proxy_url, **request_kwargs)
        except Exception as exc:
            logger.warning(
                "Request via proxy failed for {}: {}. Retrying without proxy.",
                url,
                exc,
            )

    try:
        return request_func(**request_kwargs)
    except Exception as exc:
        raise ApiRequestError(f"Request failed for {url}") from exc


def do_request(
    account_address: str,
    base_url: str,
    method: str,
    path: str,
    params: dict[str, Any],
    payload: RequestPayload,
    proxy: Proxy,
    session_id: str | None = None,
) -> ResponseData:
    method = method.upper()
    headers = _build_headers(account_address, method, path, payload, session_id)
    url = f"{base_url}?{urlencode(params)}"
    response = _send_request(method, url, headers, payload, proxy)

    if response.status_code == 429:
        raise RateLimitError(f"{account_address} | Rate limited by Debank")
    if response.status_code >= 400:
        raise ApiResponseError(
            f"{account_address} | Unexpected Debank status code: {response.status_code}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise ApiResponseError(
            f"{account_address} | Failed to decode Debank JSON response"
        ) from exc


def get_total_usd_balance(account_data: NormalizedAccountData) -> float:
    account_address, proxy = account_data
    base_url = "https://api.debank.com/asset/total_net_curve"
    params = {"user_addr": account_address.lower(), "days": 1}
    path = "/asset/total_net_curve"
    payload = {"user_addr": account_address.lower(), "days": 1}

    def operation() -> float:
        response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
        usd_value_list = response_data.get("data", {}).get("usd_value_list")
        if usd_value_list is None:
            raise ApiProtocolError(f"{account_address} | Missing usd_value_list in response")

        last_entry = usd_value_list[-1]
        if len(last_entry) < 2:
            raise RetryableOperationError(
                f"{account_address} | Incomplete USD balance response"
            )
        return float(last_entry[1])

    return retry_call(
        operation,
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} Debank total balance",
        retry_exceptions=DEBANK_RETRY_EXCEPTIONS,
    )


def get_used_chains(account_data: NormalizedAccountData, path: str) -> list[str]:
    account_address, proxy = account_data
    base_url = f"https://api.debank.com{path}"
    params = (
        {"user_addr": account_address.lower()}
        if path == "/nft/used_chains"
        else {"id": account_address.lower()}
    )
    payload = (
        {"user_addr": account_address.lower()}
        if path == "/nft/used_chains"
        else {"id": account_address.lower()}
    )

    def operation() -> list[str]:
        response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
        if path == "/nft/used_chains":
            data = response_data.get("data")
            if data is None:
                raise ApiProtocolError(f"{account_address} | Missing NFT chains in response")
            return data
        if path == "/user/used_chains":
            chains = response_data.get("data", {}).get("chains")
            if chains is None:
                raise ApiProtocolError(f"{account_address} | Missing token chains in response")
            return chains
        raise ApiProtocolError(f"{account_address} | Unsupported path: {path}")

    return retry_call(
        operation,
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} Debank used chains {path}",
        retry_exceptions=DEBANK_RETRY_EXCEPTIONS,
    )


def get_token_balances(
    account_data: NormalizedAccountData,
    chains: list[str],
) -> TokenBalancesByChain:
    account_address, proxy = account_data
    base_url = "https://api.debank.com/token/balance_list"
    path = "/token/balance_list"
    result: TokenBalancesByChain = {}

    for current_chain in chains:
        params = {"user_addr": account_address.lower(), "chain": current_chain}
        payload = {"user_addr": account_address.lower(), "chain": current_chain}

        def operation() -> list[TokenBalancesResultData]:
            response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
            response_items = response_data.get("data")
            if response_items is None:
                raise ApiProtocolError(
                    f"{account_address} | Missing token balances for chain {current_chain}"
                )

            tokens_result_data: list[TokenBalancesResultData] = []
            for token in response_items:
                token_in_usd = (token["price"] or 0) * token["amount"]
                tokens_result_data.append(
                    TokenBalancesResultData(
                        name=token["name"],
                        balance_usd=token_in_usd,
                        contract_address=token["id"],
                        amount=token["amount"],
                    )
                )
            return tokens_result_data

        result[current_chain] = retry_call(
            operation,
            attempts=5,
            initial_delay=1.0,
            backoff=2.0,
            operation_name=f"{account_address} Debank token balances {current_chain}",
            retry_exceptions=DEBANK_RETRY_EXCEPTIONS,
        )

    return result


def get_pool_balances(account_data: NormalizedAccountData) -> PoolBalancesByChain:
    account_address, proxy = account_data
    base_url = "https://api.debank.com/portfolio/project_list"
    path = "/portfolio/project_list"
    params = {"user_addr": account_address.lower()}
    payload = {"user_addr": account_address.lower()}

    def operation() -> PoolBalancesByChain:
        response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
        response_items = response_data.get("data")
        if response_items is None:
            raise ApiProtocolError(f"{account_address} | Missing pool balances in response")

        result: PoolBalancesByChain = {}
        for current_pool in response_items:
            for item in current_pool["portfolio_item_list"]:
                for token in item["asset_token_list"]:
                    if current_pool["chain"] not in result:
                        result[current_pool["chain"]] = {}
                    if current_pool["name"] not in result[current_pool["chain"]]:
                        result[current_pool["chain"]][current_pool["name"]] = []

                    token_in_usd = (token["price"] or 0) * token["amount"]
                    result[current_pool["chain"]][current_pool["name"]].append(
                        PoolBalancesResultData(
                            name=token["name"],
                            amount=token["amount"],
                            balance_usd=token_in_usd,
                        )
                    )
        return result

    return retry_call(
        operation,
        attempts=5,
        initial_delay=1.0,
        backoff=2.0,
        operation_name=f"{account_address} Debank pool balances",
        retry_exceptions=DEBANK_RETRY_EXCEPTIONS,
    )


def get_nft_balances(
    account_data: NormalizedAccountData,
    chains: list[str],
) -> NftBalancesByChain:
    account_address, proxy = account_data
    base_url = "https://api.debank.com/nft/collection_list"
    path = "/nft/collection_list"
    result: NftBalancesByChain = {}

    for current_chain in chains:
        params = {"user_addr": account_address.lower(), "chain": current_chain}
        payload = {"user_addr": account_address.lower(), "chain": current_chain}

        def operation() -> list[NftBalancesResultData]:
            response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
            response_payload = response_data.get("data", {})
            job = response_payload.get("job")
            if job and job.get("status") == "pending":
                raise RetryableOperationError(
                    f"{account_address} | NFT balance job is still pending"
                )

            nft_items = response_payload.get("result", {}).get("data")
            if nft_items is None:
                raise ApiProtocolError(
                    f"{account_address} | Missing NFT balances for chain {current_chain}"
                )

            nft_result: list[NftBalancesResultData] = []
            for current_nft_data in nft_items:
                nft_in_usd = (
                    (current_nft_data["spent_token"]["price"] or Decimal(0))
                    * current_nft_data["avg_price_last_24h"]
                    * current_nft_data["amount"]
                )
                nft_result.append(
                    NftBalancesResultData(
                        name=current_nft_data["name"],
                        amount=current_nft_data["amount"],
                        balance_usd=nft_in_usd,
                    )
                )
            return nft_result

        result[current_chain] = retry_call(
            operation,
            attempts=8,
            initial_delay=3.0,
            backoff=1.0,
            operation_name=f"{account_address} Debank NFT balances {current_chain}",
            retry_exceptions=DEBANK_RETRY_EXCEPTIONS,
        )

    return result


def _normalize_account_data(
    account_data: RawAccountData,
) -> tuple[str, Proxy, NormalizedAccountData]:
    account_entry, proxy = account_data
    if isinstance(account_entry, dict) and "wallet" in account_entry:
        account_address = str(account_entry["wallet"].address)
    else:
        account_address = account_entry.strip()

    normalized_account_data: NormalizedAccountData = (account_address, proxy)
    return account_address, proxy, normalized_account_data


def parse_debank_account(
    account_data: RawAccountData,
    config: ConfigStruct,
) -> AccountProcessingResult:
    account_address, _proxy, normalized_account_data = _normalize_account_data(account_data)
    debank_config = config.debank_config

    total_usd_balance = get_total_usd_balance(normalized_account_data)
    logger.info("{} | Total USD Balance: {}$", account_address, total_usd_balance)

    token_balances: TokenBalancesByChain = {}
    nft_balances: NftBalancesByChain = {}
    pools_data: PoolBalancesByChain = {}
    token_chains_used: list[str] = []
    nft_chains_used: list[str] = []

    if debank_config.parse_tokens:
        token_chains_used = get_used_chains(normalized_account_data, "/user/used_chains")
        logger.info("{} | Token Chains Used: {}", account_address, len(token_chains_used))
        if token_chains_used:
            token_balances = get_token_balances(normalized_account_data, token_chains_used)
            logger.info("{} | Successfully Parsed Tokens", account_address)

    if debank_config.parse_nfts:
        nft_chains_used = get_used_chains(normalized_account_data, "/nft/used_chains")
        logger.info("{} | NFT Chains Used: {}", account_address, len(nft_chains_used))
        if nft_chains_used:
            nft_balances = get_nft_balances(normalized_account_data, nft_chains_used)
            logger.info("{} | Successfully Parsed NFTs", account_address)

    if debank_config.parse_pools:
        pools_data = get_pool_balances(normalized_account_data)
        logger.info("{} | Successfully Parsed Pools", account_address)

    formatted_result = format_result(
        config,
        normalized_account_data,
        account_address,
        total_usd_balance,
        token_chains_used,
        nft_chains_used,
        token_balances,
        nft_balances,
        pools_data,
    )

    return AccountProcessingResult(
        account_address=account_address,
        total_balance=float(total_usd_balance),
        files=[formatted_result],
    )
