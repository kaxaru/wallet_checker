from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class RequestParamsStruct(BaseModel):
    account_header: str
    nonce: str
    signature: str
    timestamp: str

class Info(BaseModel):
    random_at: int
    random_id: str
    user_addr: Optional[str]

class RequestSessionStruct(Info):
    session_id: str
    wallet_type: str
    is_verified: bool


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
    two_captcha_apikey: str