import json
import time
import requests
from requests import Session
from decimal import Decimal
from tasks.client import get_client
from utils.generateSignature import generate_signature
from utils.getFile import read_file
from urllib.parse import urlencode
from pyuseragents import random as random_useragent
from utils.debankResult import format_result

# class CustomBigFloat:
#     def __init__(self, value=None):
#         self.value = value or Decimal(0)
#
#     def from_json(self, json_data):
#         if isinstance(json_data, str):
#             self.value = Decimal(json_data)
#         else:
#             self.value = Decimal(json_data)
#
#     def to_json(self):
#         return str(self.value)


def do_request(account_address, base_url, method, path, params, payload, proxy, sessionId = None):

    client = get_client(proxy)

    if method.upper() == "POST":
        if payload is not None:
            try:
                body = json.dumps(payload)
            except Exception as e:
                raise Exception(f"{account_address} | Failed to marshal payload: {e}")

        try:
            debank_params = generate_signature({}, method.upper(), path)
            account_header, nonce, signature, timestamp = debank_params.values()
        except Exception as e:
            raise Exception(f"{account_address} | Failed to generate request params: {e}")
    else:
        try:
            debank_params  = generate_signature(payload, method.upper(), path)
            account_header, nonce, signature, timestamp = debank_params.values()
        except Exception as e:
            raise Exception(f"{account_address} | Failed to generate request params: {e}")


    if not sessionId == None:
        try:
            acc = json.loads(account_header)
            acc["user_addr"] = account_address.lower()
            acc["session_id"] =  sessionId
            acc["wallet_type"] = "metamask"
            acc["is_verified"] = True
        except Exception as e:
            print(f"{account_address} | Error decoding account headers: {e}")

        account_header = acc
        account_header  = json.dumps(account_header)

    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,be;q=0.6,zh-CN;q=0.5,zh;q=0.4,uk;q=0.3',
        'origin': 'https://debank.com',
        'referer': 'https://debank.com/',
        'source': 'web',
        'x-api-ver': 'v2',
        'account': account_header,
        'x-api-nonce': nonce,
        'x-api-sign': signature,
        'x-api-ts': timestamp,
        "user-agent": random_useragent()
    }

    url = f"{base_url}?{urlencode(params)}"
    response = None

    if method.upper() == 'POST':
        headers['Content-Type'] = 'application/json'
        response = client.post(url, headers=headers, data=json.dumps(payload))
    else:
        response = client.get(url, headers=headers)

    if response.status_code == 429:
        raise Exception(f"{account_address} | Rate limit")

    return response.json()


def get_total_usd_balance(account_address):
    account_address, proxy = account_address

    base_url = "https://api.debank.com/asset/total_net_curve"
    params = {'user_addr': account_address.lower(), 'days': 1}
    path = f"/asset/total_net_curve"

    payload = {'user_addr': account_address.lower(), 'days': 1}

    while True:
        try:
            response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
            usd_value_list = response_data['data']['usd_value_list']
            if len(usd_value_list) < 1:
                return 0
            last_entry = usd_value_list[-1]
            if len(last_entry) < 2:
                continue
            return last_entry[1]
        except Exception as e:
            print(f"{account_address} | Error: {e}")
            continue


def get_used_chains(account_address, path):
    account_address, proxy = account_address
    base_url = f"https://api.debank.com{path}"
    params = {'user_addr': account_address.lower()} if path == "/nft/used_chains" else {'id': account_address.lower()}
    payload = {'user_addr': account_address.lower()} if path == "/nft/used_chains" else {'id': account_address.lower()}

    while True:
        try:
            response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
            if path == "/nft/used_chains":
                return response_data['data']
            elif path == "/user/used_chains":
                return response_data['data']['chains']
        except Exception as e:
            print(f"{account_address} | Error: {e}")
            continue


def get_token_balances(account_address, chains):
    account_address, proxy = account_address
    base_url = "https://api.debank.com/token/balance_list"
    path = "/token/balance_list"
    result = {}

    for current_chain in chains:
        params = {'user_addr': account_address.lower(), 'chain': current_chain}
        payload = {'user_addr': account_address.lower(), 'chain': current_chain}

        while True:
            try:
                response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
                tokens_result_data = []
                for token in response_data['data']:
                    token_in_usd = (token['price'] or 0) * token['amount']
                    tokens_result_data.append({
                        'name': token['name'],
                        'balance_usd': token_in_usd,
                        'contract_address': token['id'],
                        'amount': token['amount']
                    })
                result[current_chain] = tokens_result_data
                break
            except Exception as e:
                print(f"{account_address} | Error: {e}")
                continue

    return result


def get_pool_balances(account_address):
    account_address, proxy = account_address
    base_url = "https://api.debank.com/portfolio/project_list"
    path = "/portfolio/project_list"
    result = {}

    params = {'user_addr': account_address.lower()}
    payload = {'user_addr': account_address.lower()}

    while True:
        try:
            response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
            for current_pool in response_data['data']:
                for item in current_pool['portfolio_item_list']:
                    for token in item['asset_token_list']:
                        if current_pool['chain'] not in result:
                            result[current_pool['chain']] = {}
                        if current_pool['name'] not in result[current_pool['chain']]:
                            result[current_pool['chain']][current_pool['name']] = []

                        token_in_usd = (token['price'] or 0) * token['amount']
                        result[current_pool['chain']][current_pool['name']].append({
                            'name': token['name'],
                            'amount': token['amount'],
                            'balance_usd': token_in_usd,
                        })
            break
        except Exception as e:
            print(f"{account_address} | Error: {e}")
            continue

    return result


def get_nft_balances(account_address, chains):
    account_address, proxy = account_address
    base_url = "https://api.debank.com/nft/collection_list"
    path = "/nft/collection_list"
    result = {}

    params = {'user_addr': account_address.lower()}

    for current_chain in chains:
        while True:
            try:
                params['chain'] = current_chain
                payload = {'user_addr': account_address.lower(), 'chain': current_chain}
                response_data = do_request(account_address, base_url, "GET", path, params, payload, proxy)
                if response_data['data']['job'] and response_data['data']['job']['status'] == "pending":
                    print(f"{account_address} | NFT Balance Pending, sleeping 3 secs...")
                    time.sleep(3)
                    continue

                for current_nft_data in response_data['data']['result']['data']:
                    nft_in_usd = (current_nft_data['spent_token']['price'] or Decimal(0)) * current_nft_data['avg_price_last_24h'] * current_nft_data['amount']
                    result[current_chain] = result.get(current_chain, [])
                    result[current_chain].append({
                        'name': current_nft_data['name'],
                        'amount': current_nft_data['amount'],
                        'balance_usd': nft_in_usd,
                    })
                break
            except Exception as e:
                print(f"{account_address} | Error: {e}")
                continue

    return result


def parse_debank_account(account_data):
    try:
        CONFIG_FILE = read_file("./data/config.json", is_json=True)
        debank_config = CONFIG_FILE['debank_config']

        if 'wallet' in account_data[0]:
            account_address = account_data[0]['wallet'].address
            proxy = account_data[1]

            account_data = list((account_address, proxy))

        else:
            account_address = account_data[0].strip()  # Example: assuming account_data is just address here
        total_usd_balance = get_total_usd_balance(account_data)
        print(f"{account_address} | Total USD Balance: {total_usd_balance}$")

        token_balances, nft_balances, pools_data = {}, {}, {}
        token_chains_used, nft_chains_used = {}, {}

        if debank_config['parse_tokens']:
            token_chains_used = get_used_chains(account_data, "/user/used_chains")
            print(f"{account_address} | Token Chains Used: {len(token_chains_used)}")

            if token_chains_used :
                token_balances = get_token_balances(account_data, token_chains_used)
                print(f"{account_address} | Successfully Parsed Tokens")


        if debank_config['parse_nfts']:
            nft_chains_used = get_used_chains(account_data, "/nft/used_chains")
            print(f"{account_address} | NFT Chains Used: {len(nft_chains_used)}")
            if nft_chains_used:
                nft_balances = get_nft_balances(account_data, nft_chains_used)
                print(f"{account_address} | Successfully Parsed NFTs")

        if debank_config['parse_pools']:
            pools_data = get_pool_balances(account_data)
            print(f"{account_address} | Successfully Parsed Pools")


        format_result(CONFIG_FILE, account_data, account_address, total_usd_balance, token_chains_used, nft_chains_used, token_balances, nft_balances, pools_data)

    except Exception as e:
        print(f"Error parsing account: {e}")
