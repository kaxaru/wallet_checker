from pathlib import Path

from app.utils.getFile import read_file

PROXY_FILE = Path("data/connection.txt")


def get_proxies(format_proxy: str = "socks5") -> list[dict[str, str]]:
    raw_proxies = read_file(str(PROXY_FILE), check_empty=False)

    proxies: list[dict[str, str]] = []
    for raw_proxy in raw_proxies:
        if not raw_proxy:
            continue

        host, port, login, password = raw_proxy.split(":", maxsplit=3)
        formatted_proxy = f"{login}:{password}@{host}:{port}"
        proxies.append(
            {
                "http": f"{format_proxy}://{formatted_proxy}",
                "https": f"{format_proxy}://{formatted_proxy}",
            }
        )

    return proxies
