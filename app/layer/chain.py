from eth_typing import HexStr
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3
from web3.middleware import Middleware

from app.layer.caip2chaindata import Explorer, NativeCurrency


class Chain(Web3):
    provider: HTTPProvider

    def __init__(
        self,
        rpc: str,
        rpcs: list[str],
        id: int,
        *,
        explorers: list[Explorer] | None = None,
        name: str | None = None,
        short_name: str | None = None,
        title: str | None = None,
        info_url: str | None = None,
        native_currency: NativeCurrency | None = None,
        eip1559: bool = True,
        provider_timeout: int = 15,
        proxy: str | None = None,
        use_poa_middleware: bool = True,
    ) -> None:
        self.explorers = explorers or []
        self.id = id
        self.name = name
        self.short_name = short_name
        self.title = title
        self.info_url = info_url
        self.native_currency = native_currency or NativeCurrency()
        self.eip1559 = eip1559
        http_provider = HTTPProvider(rpc, request_kwargs={"timeout": provider_timeout})
        http_provider.cache_allowed_requests = True
        super().__init__(provider=http_provider)

        if use_poa_middleware:
            self.middleware_onion.inject(Middleware, layer=0)

        self.proxy = proxy

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        if self.provider is not None:
            return f"{self.__class__.__name__}(rpc={self.provider.endpoint_uri}, name={self.name})"
        return f"{self.__class__.__name__}(rpc={self.rpc}, name={self.name})"

    def tx_urls(self, tx_hash: HexBytes | HexStr | str) -> list[tuple[Explorer, str]]:
        if isinstance(tx_hash, HexBytes):
            tx_hash = tx_hash.hex()

        return [(explorer, explorer.tx_url(tx_hash)) for explorer in self.explorers]
