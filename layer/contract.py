from eth_typing import ChecksumAddress
import os
import json
from web3 import Web3
from loguru import logger
from enum import Enum

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
    def __init__(self, web3: Web3, abi: str = '', address: ChecksumAddress = None):
        self.contract = self.load_contract(web3, abi, address) #name?

    def load_contract(self, web3, abi_name, address):
        address = web3.toChecksumAddress(address)
        return web3.eth.contract(address=address, abi=self._load_abi(abi_name))

    def _load_abi(self, name):
        path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
        with open(os.path.abspath(path + f"{name}.json")) as f:
            abi: str = json.load(f)
        return abi

    def isExitChain(self, chainId):
        _all = [Chains, Chains_testnets]
        name = 'None'
        for _ in _all:
            try:
                name = Chains(chainId).name
                break
            except Exception as e:
                logger.error(e)

        return name

    def __repr__(self):
        chainId = self.chain.eth.chainId
        return f"{self.__class__.__name__}(address={self.contract.address}, chain.name={self.isExitChain(chainId)})"
