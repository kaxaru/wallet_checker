from web3 import Web3
import os


RPCS = {
    'eth' : {'chain': 'ETH', 'chain_id': 1, 'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx', 'token': 'ETH'},

    'optimism' : {'chain': 'OPTIMISM', 'chain_id': 10, 'rpc': 'https://rpc.ankr.com/optimism', 'scan': 'https://optimistic.etherscan.io/tx', 'token': 'ETH'},

    'bsc' : {'chain': 'BSC', 'chain_id': 56, 'rpc': 'https://rpc.ankr.com/bsc', 'scan': 'https://bscscan.com/tx', 'token': 'BNB'},

    'polygon' : {'chain': 'MATIC', 'chain_id': 137, 'rpc': 'https://polygon-rpc.com', 'scan': 'https://polygonscan.com/tx', 'token': 'MATIC'},

    'arbitrum' : {'chain': 'ARBITRUM', 'chain_id': 42161, 'rpc': 'https://rpc.ankr.com/arbitrum', 'scan': 'https://arbiscan.io/tx', 'token': 'ETH'},

    'avaxc' : {'chain': 'AVAXC', 'chain_id': 43114, 'rpc': 'https://rpc.ankr.com/avalanche', 'scan': 'https://snowtrace.io/tx', 'token': 'AVAX'},

    'fantom' : {'chain': 'FANTOM', 'chain_id': 250, 'rpc': 'https://rpc.ankr.com/fantom', 'scan': 'https://ftmscan.com/tx', 'token': 'FTM'},

    'celo' : {'chain': 'CELO', 'chain_id': 42220, 'rpc': 'https://rpc.ankr.com/celo', 'scan': 'https://celoscan.io/tx', 'token': 'CELO'},

}

def get_main_wallet():
    with open(f'{os.path.dirname(__file__)}/../wallets/wallets.txt', 'r') as file:
        _main_wallet = [row.strip() for row in file]
    return _main_wallet

def get_all_wallets(list):
    web3 = Web3(Web3.HTTPProvider(RPCS["optimism"]["rpc"]))
    web3.eth.account.enable_unaudited_hdwallet_features()
    _wallets = []
    for wallet in list:
        if len(wallet) == 0:
            continue
        if len(wallet) == 64:
            cWallet = web3.eth.account.from_key(wallet)
            _wallets.append({'wallet': cWallet})
        else:
            wallet_format = wallet.split(';')
            if len(wallet_format) == 2:
                num_of_wallet = wallet_format[1]
            elif len(wallet_format) == 3:
                _indexes = wallet_format[2].split(',')
                indexes = []
                for _ind in _indexes:
                    if _ind == '':
                        continue
                    if len(_ind) > 1 and len(_ind.split('-')) == 2:
                        els = _ind.split('-')
                        _start = int(els[0])
                        _finish = int(els[1])
                        for i in range(_start, _finish):
                            indexes.append(i)
                    else:
                        indexes.append(int(_ind))
            else:
                num_of_wallet = 100
            cWallet = wallet_format[0]
            if len(wallet_format) == 3:
                num_of_wallet = indexes[len(indexes) - 1]
                _all_wallets = []
                for i in range(int(num_of_wallet)):
                    wallet_address = web3.eth.account.from_mnemonic(cWallet, account_path=f"m/44'/60'/0'/0/{i}")
                    _all_wallets.append({'wallet': wallet_address})
                _new_wallets = []
                for el in indexes:
                    _new_wallets.append(_all_wallets[el - 1])
                [_wallets.append(_new) for _new in _new_wallets]
            else:
                for i in range(int(num_of_wallet)):
                    wallet_address = web3.eth.account.from_mnemonic(cWallet, account_path=f"m/44'/60'/0'/0/{i}")
                    _wallets.append({'wallet': wallet_address})

    return _wallets