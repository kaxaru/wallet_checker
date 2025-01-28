import json
import logging
import requests
from urllib.parse import urlencode
from operator import itemgetter


def sort_by_chain_balance(data):
    return sorted(data, key=itemgetter("ChainBalance"), reverse=True)

def get_total_balance(account_address, proxy):
    base_url = "https://api.rabby.io/v1/user/total_balance"
    params = {"id": account_address}

    class RabbyReturnData:
        def __init__(self, chain_name, chain_balance):
            self.chain_name = chain_name
            self.chain_balance = chain_balance

    for _ in range(10):
        try:
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "ru,en;q=0.9"
            }

            response = requests.get(
                f"{base_url}?{urlencode(params)}",
                headers=headers,
                proxies=proxy,
                timeout=15
            )

            if response.status_code in {429, 403}:
                logging.warning(f"{account_address} | Rate Limited")
                continue

            response_data = response.json()

            if response_data.get("message") == "Too Many Requests":
                logging.warning(f"{account_address} | Rate Limited")
                continue

            total_usd_balance = response_data["total_usd_value"]
            chain_balances = []

            for current_chain in response_data["chain_list"]:
                if current_chain["usd_value"] <= 0:
                    continue
                chain_balances.append(RabbyReturnData(
                    chain_name=current_chain["name"],
                    chain_balance=current_chain["usd_value"]
                ))

            return total_usd_balance, chain_balances

        except requests.RequestException as e:
            logging.error(f"{account_address} | Request Error: {e}")
            continue

    return 0, []


def parse_rabby_account(account_data):
    account_address, proxy = account_data

    if 'wallet' in account_address:
        account_address = account_address['wallet'].address

    total_usd_balance, chain_balances = get_total_balance(account_address, proxy)
    sorted_chain_balances = sort_by_chain_balance([
        {"ChainName": chain.chain_name, "ChainBalance": chain.chain_balance}
        for chain in chain_balances
    ])

    formatted_result = f"Address: {account_address}\nTotal Balance: {total_usd_balance:.2f} $\n\n"
    for chain in sorted_chain_balances:
        formatted_result += f"{chain['ChainName']} | {chain['ChainBalance']:.2f} $\n"
    formatted_result += "\n\n"

    print(f"{account_address} | Total USD Balance: {total_usd_balance:.2f} $")

    if 0 <= total_usd_balance < 1:
        file_path = "0_1_rabby.txt"
    elif 1 <= total_usd_balance < 10:
        file_path = "1_10_rabby.txt"
    elif 10 <= total_usd_balance < 100:
        file_path = "10_100_rabby.txt"
    elif 100 <= total_usd_balance < 500:
        file_path = "100_500_rabby.txt"
    elif 500 <= total_usd_balance < 1000:
        file_path = "500_1000_rabby.txt"
    else:
        file_path = "1000_plus_rabby.txt"

    append_to_file(f"./results/{file_path}", formatted_result)

def append_to_file(filename: str, data: str):
    with open(filename, "a") as file:
        file.write(data)