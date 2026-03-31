import os

def get_address():
    with open(f'{os.path.dirname(__file__)}/../wallets/address.txt', 'r') as file:
        _addresses = [row.strip() for row in file]
    return _addresses