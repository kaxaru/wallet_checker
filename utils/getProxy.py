import os

def get_proxies(format_proxy="socks5"):
    with open(f'{os.path.dirname(__file__)}/../data/connection.txt', 'r') as file:
        _proxies = [row.strip() for row in file]

    proxies = []
    for _pr in _proxies:
        _format = f"{_pr.split(':')[2]}:{_pr.split(':')[3]}@{_pr.split(':')[0]}:{_pr.split(':')[1]}"
        _pr = {
            'http': f"{format_proxy}://{_format}",
            'https': f"{format_proxy}://{_format}"
        }
        proxies.append(_pr)

    return proxies