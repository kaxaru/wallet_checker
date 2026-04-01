from pathlib import Path

from web3 import Web3

from app.utils.getFile import read_file

WALLETS_FILE = Path("wallets/wallets.txt")
RPCS = {
    "eth": {
        "chain": "ETH",
        "chain_id": 1,
        "rpc": "https://rpc.ankr.com/eth",
        "scan": "https://etherscan.io/tx",
        "token": "ETH",
    },
    "optimism": {
        "chain": "OPTIMISM",
        "chain_id": 10,
        "rpc": "https://rpc.ankr.com/optimism",
        "scan": "https://optimistic.etherscan.io/tx",
        "token": "ETH",
    },
    "bsc": {
        "chain": "BSC",
        "chain_id": 56,
        "rpc": "https://rpc.ankr.com/bsc",
        "scan": "https://bscscan.com/tx",
        "token": "BNB",
    },
    "polygon": {
        "chain": "MATIC",
        "chain_id": 137,
        "rpc": "https://polygon-rpc.com",
        "scan": "https://polygonscan.com/tx",
        "token": "MATIC",
    },
    "arbitrum": {
        "chain": "ARBITRUM",
        "chain_id": 42161,
        "rpc": "https://rpc.ankr.com/arbitrum",
        "scan": "https://arbiscan.io/tx",
        "token": "ETH",
    },
    "avaxc": {
        "chain": "AVAXC",
        "chain_id": 43114,
        "rpc": "https://rpc.ankr.com/avalanche",
        "scan": "https://snowtrace.io/tx",
        "token": "AVAX",
    },
    "fantom": {
        "chain": "FANTOM",
        "chain_id": 250,
        "rpc": "https://rpc.ankr.com/fantom",
        "scan": "https://ftmscan.com/tx",
        "token": "FTM",
    },
    "celo": {
        "chain": "CELO",
        "chain_id": 42220,
        "rpc": "https://rpc.ankr.com/celo",
        "scan": "https://celoscan.io/tx",
        "token": "CELO",
    },
}


def get_main_wallet() -> list[str]:
    return read_file(str(WALLETS_FILE), check_empty=False)


def get_all_wallets(wallet_rows: list[str]) -> list[dict[str, object]]:
    web3 = Web3(Web3.HTTPProvider(RPCS["optimism"]["rpc"]))
    web3.eth.account.enable_unaudited_hdwallet_features()
    wallets: list[dict[str, object]] = []

    for wallet_row in wallet_rows:
        if not wallet_row:
            continue

        if len(wallet_row) == 64:
            current_wallet = web3.eth.account.from_key(wallet_row)
            wallets.append({"wallet": current_wallet})
            continue

        wallet_format = wallet_row.split(";")
        if len(wallet_format) == 2:
            num_of_wallet = wallet_format[1]
        elif len(wallet_format) == 3:
            raw_indexes = wallet_format[2].split(",")
            indexes: list[int] = []
            for raw_index in raw_indexes:
                if raw_index == "":
                    continue
                if len(raw_index) > 1 and len(raw_index.split("-")) == 2:
                    start, finish = raw_index.split("-")
                    for index in range(int(start), int(finish)):
                        indexes.append(index)
                else:
                    indexes.append(int(raw_index))
        else:
            num_of_wallet = 100

        mnemonic = wallet_format[0]
        if len(wallet_format) == 3:
            num_of_wallet = indexes[-1]
            derived_wallets = []
            for index in range(int(num_of_wallet)):
                wallet_address = web3.eth.account.from_mnemonic(
                    mnemonic,
                    account_path=f"m/44'/60'/0'/0/{index}",
                )
                derived_wallets.append({"wallet": wallet_address})
            for index in indexes:
                wallets.append(derived_wallets[index - 1])
        else:
            for index in range(int(num_of_wallet)):
                wallet_address = web3.eth.account.from_mnemonic(
                    mnemonic,
                    account_path=f"m/44'/60'/0'/0/{index}",
                )
                wallets.append({"wallet": wallet_address})

    return wallets
