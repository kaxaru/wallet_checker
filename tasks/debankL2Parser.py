import json
import requests
import logging
from eth_account import Account
from web3 import Web3
from .debankParser import do_request
from utils.getResultCaptha import solve_captcha
from eth_account.messages import encode_defunct

def get_sign_l2(account_address: str, proxy: dict) -> str:
    base_url = "https://api.debank.com/user/sign_v2"
    path = "/user/sign_v2"

    payload = {
        "id": account_address.lower(),
        "chain_id": "1"
    }

    while True:
        response = do_request(account_address, base_url, "POST", path, {}, payload, proxy)

        if response is None:
            continue

        if response.get('error_code') != 0:
            logging.error(f"{account_address} | Ошибка при разборе JSON-ответа")
            continue

        return response["data"]["text"]


def sign_message(message_text: str, private_key_hex: str) -> str:
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    validate_msg = encode_defunct(text=message_text)
    signature = web3.eth.account.sign_message(validate_msg, private_key=private_key_hex)
    return signature.signature.hex()


def do_auth(account_address: str, captcha_response: str, signed_message: str, proxy: dict) -> str:
    base_url = "https://api.debank.com/user/login_v2"
    path = "/user/login_v2"

    payload = {
        "token": captcha_response,
        "id": account_address.lower(),
        "chain_id": "1",
        "signature": signed_message
    }

    while True:
        response = do_request(account_address, base_url, "POST", path, {}, payload, proxy)

        if response is None:
            continue


        if response.get('error_code') != 0:
            logging.error(f"{account_address} | Ошибка при разборе JSON-ответа")
            continue

        return response["data"]["session_id"]


def get_l2_balance(account_address: str, session_id: str, proxy: dict) -> float:
    base_url = "https://api.debank.com/user/l2_account"
    path = "/user/l2_account"

    payload = {
        "id": account_address.lower()
    }

    params = {
        "id": account_address.lower()
    }


    while True:
        response = do_request(account_address, base_url, "GET", path, params, payload, proxy, session_id)

        if response is None:
            continue


        if response.get('error_code') != 0:
            logging.error(f"{account_address} | Ошибка при разборе JSON-ответа")
            continue

        return response["data"]["balance"]


def debank_l2_balance_parser(account_data: str):
    account, proxy = account_data
    account_address = account['wallet'].address
    private_key = account['wallet'].privateKey

    message_text = get_sign_l2(account_address, proxy)
    message_signed = sign_message(message_text, private_key.hex())
    captcha_response = solve_captcha(account_address)

    session_id = do_auth(account_address, captcha_response, message_signed, proxy)
    account_balance = get_l2_balance(account_address, session_id, proxy)

    logging.info(f"{account_address} | Баланс: {account_balance} $")

    if account_balance > 0:
        append_to_file("./results/debank_l2_balances.txt",
                       f"{account_address} | {account_balance} $\n")

def append_to_file(filename: str, data: str):
    with open(filename, "a") as file:
        file.write(data)