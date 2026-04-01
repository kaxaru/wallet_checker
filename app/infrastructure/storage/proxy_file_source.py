from app.utils.getProxy import get_proxies


class FileProxySource:
    def __init__(self, proxy_format: str = "http") -> None:
        self._proxy_format = proxy_format

    def load_proxies(self) -> list[dict[str, str] | None]:
        return get_proxies(format_proxy=self._proxy_format) or [None]
