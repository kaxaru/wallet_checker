import os
import json

def get_keys(data):
    return list(data.keys())


def format_result(config, account_data, account_address, total_usd_balance, tokens_chains_count,
                  nft_chains_count, token_balances, nft_balances, pools_data):

    debank_config = config['debank_config']
    """Форматирует и записывает результаты в зависимости от баланса."""
    formatted_result = ""

    formatted_result += f"==================== Address: {account_address} ({total_usd_balance} $ | tokens chains: {tokens_chains_count} | nft chains: {nft_chains_count})\n"
    formatted_result += f"==================== Account Data: {account_data}\n"

    # Форматирование балансов токенов
    if debank_config["parse_tokens"] and len(token_balances) > 0:
        total_tokens = sum(len(tokens) for tokens in token_balances.values())
        formatted_result += f"\n========== Token Balances ({total_tokens} tokens)\n"

        for chain_name in get_keys(token_balances):
            if len(token_balances[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(token_balances[chain_name])} tokens)\n"

            for token_data in token_balances[chain_name]:
                formatted_result += (f"    Name: {token_data['name']} | Balance (in usd): {token_data['balance_usd']} $ "
                                     f"| Amount: {token_data['amount']} | CA: {token_data['contract_address']}\n")
            formatted_result += "\n"

    # Форматирование NFT-балансов
    if debank_config["parse_nfts"] and len(nft_balances) > 0:
        total_nfts = sum(len(nfts) for nfts in nft_balances.values())
        formatted_result += f"\n========== NFT Balances ({total_nfts} nfts)\n"

        for chain_name in get_keys(nft_balances):
            if len(nft_balances[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(nft_balances[chain_name])} nfts)\n"

            for nft_data in nft_balances[chain_name]:
                formatted_result += (f"    Name: {nft_data['name']} | Price (in usd): {nft_data['balance_usd']} $ "
                                     f"| Amount: {nft_data['amount']}\n")
            formatted_result += "\n"

    # Форматирование данных пулов
    if debank_config["parse_pools"] and len(pools_data) > 0:
        total_pools = sum(len(pool) for chain in pools_data.values() for pool in chain.values())
        formatted_result += f"\n========== Pool Balances ({total_pools} pools)\n"

        for chain_name in get_keys(pools_data):
            if len(pools_data[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(pools_data[chain_name])} pools)\n"

            for pool_name in get_keys(pools_data[chain_name]):
                if len(pools_data[chain_name][pool_name]) < 1:
                    continue

                formatted_result += f"===== {pool_name.upper()}\n"

                for pool_data in pools_data[chain_name][pool_name]:
                    formatted_result += (f"    Name: {pool_data['name']} | Balance (in usd): {pool_data['balance_usd']} $ "
                                         f"| Amount: {pool_data['amount']}\n")
                formatted_result += "\n"

    formatted_result += "\n\n\n"

    # Выбор файла в зависимости от баланса
    if 0 <= total_usd_balance < 1:
        file_path = "0_1_debank.txt"
    elif 1 <= total_usd_balance < 10:
        file_path = "1_10_debank.txt"
    elif 10 <= total_usd_balance < 100:
        file_path = "10_100_debank.txt"
    elif 100 <= total_usd_balance < 500:
        file_path = "100_500_debank.txt"
    elif 500 <= total_usd_balance < 1000:
        file_path = "500_1000_debank.txt"
    else:
        file_path = "1000_plus_debank.txt"

    append_file(f"./results/{file_path}", formatted_result)


def append_file(file_path, content):
    """Дописывает данные в файл."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(content)
