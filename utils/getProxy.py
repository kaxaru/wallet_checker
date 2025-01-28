import os

def get_proxies():
    with open(f'{os.path.dirname(__file__)}/../data/connection.txt', 'r') as file:
        _proxies = [row.strip() for row in file]


    proxies = []
    for _pr in _proxies:
        _format = f"{_pr.split(':')[2]}:{_pr.split(':')[3]}@{_pr.split(':')[0]}:{_pr.split(':')[1]}"
        _pr = {
            'http': f"socks5://{_format}",
            'https': f"socks5://{_format}"
        }
        proxies.append(_pr)

    return proxies