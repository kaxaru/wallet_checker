import json
from enum import Enum
from pathlib import Path
from typing import Any

from eth_typing import ChecksumAddress
from loguru import logger
from web3 import Web3

ABI_DIR = Path("app/layer/assets")


class Chains(Enum):
    ETH = 1
    BSC = 56
    OPTIMISM = 10
    POLYGON = 137
    ARBITRUM = 42161
    AVAXC = 43114
    FANTOM = 250
    CELO = 42220
    HARMONY = 1666600000
    XDAI = 100
    CORE = 1116
    OPBNB = 204


class Chains_testnets(Enum):
    SEPOLIA_ETH = 11155111
    SEPOLIA_BASE = 84532
    SEPOLIA_OPTIMISM = 11155420
    SEPOLIA_ARBITRUM = 421614
    SEPOLIA_LINEA = 59141
    SEPOLIA_MANTLE = 50031
    MITOSIS = 124832


class Contract:
    def __init__(
        self,
        web3: Web3,
        abi: str = "",
        address: ChecksumAddress | str | None = None,
    ) -> None:
        self.chain = web3
        self.contract = self.load_contract(web3, abi, address)

    def load_contract(
        self,
        web3: Web3,
        abi_name: str,
        address: ChecksumAddress | str | None,
    ) -> Any:
        checksum_address = web3.to_checksum_address(address)
        return web3.eth.contract(address=checksum_address, abi=self._load_abi(abi_name))

    def _load_abi(self, name: str) -> Any:
        with (ABI_DIR / f"{name}.json").open(encoding="utf-8") as file:
            abi: Any = json.load(file)
        return abi

    def isExitChain(self, chainId: int) -> str:
        all_chains = [Chains, Chains_testnets]
        name = "None"
        for chain_group in all_chains:
            try:
                name = chain_group(chainId).name
                break
            except Exception as exc:
                logger.error(exc)

        return name

    def __repr__(self) -> str:
        chainId = self.chain.eth.chain_id
        return f"{self.__class__.__name__}(address={self.contract.address}, chain.name={self.isExitChain(chainId)})"
