from decimal import Decimal
from pydantic import BaseModel


class RequestParamsStruct(BaseModel):
    account_header: str
    nonce: str
    signature: str
    timestamp: str


class TokenBalancesResultData(BaseModel):
    amount: Decimal
    name: str
    contract_address: str
    balance_usd: Decimal


class PoolBalancesResultData(BaseModel):
    amount: Decimal
    name: str
    balance_usd: Decimal


class NftBalancesResultData(BaseModel):
    amount: Decimal
    name: str
    balance_usd: Decimal


class RabbyReturnData(BaseModel):
    chain_name: str
    chain_balance: float


class DebankConfig(BaseModel):
    parse_tokens: bool
    parse_nfts: bool
    parse_pools: bool


class ConfigStruct(BaseModel):
    debank_config: DebankConfig
    two_captcha_api_key: str