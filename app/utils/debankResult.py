from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, TypeAlias

from app.domain.models import ResultFile
from app.layer.debankType import (
    ConfigStruct,
    NftBalancesResultData,
    PoolBalancesResultData,
    TokenBalancesResultData,
)
from app.utils.result_sink import build_bucketed_result_file_name

AccountData: TypeAlias = tuple[str, dict[str, str] | None]
TokenBalancesByChain: TypeAlias = Mapping[str, Sequence[TokenBalancesResultData]]
NftBalancesByChain: TypeAlias = Mapping[str, Sequence[NftBalancesResultData]]
PoolBalancesByChain: TypeAlias = Mapping[str, Mapping[str, Sequence[PoolBalancesResultData]]]


def get_keys(data: Mapping[str, Any]) -> list[str]:
    return list(data.keys())


def format_result(
    config: ConfigStruct,
    account_data: AccountData,
    account_address: str,
    total_usd_balance: float | Decimal,
    token_chains: Sequence[str],
    nft_chains: Sequence[str],
    token_balances: TokenBalancesByChain,
    nft_balances: NftBalancesByChain,
    pools_data: PoolBalancesByChain,
) -> ResultFile:
    debank_config = config.debank_config
    formatted_result = ""

    formatted_result += (
        f"==================== Address: {account_address} ({total_usd_balance} $ "
        f"| tokens chains: {len(token_chains)} | nft chains: {len(nft_chains)})\n"
    )
    formatted_result += f"==================== Account Data: {account_data}\n"

    if debank_config.parse_tokens and len(token_balances) > 0:
        total_tokens = sum(len(tokens) for tokens in token_balances.values())
        formatted_result += f"\n========== Token Balances ({total_tokens} tokens)\n"

        for chain_name in get_keys(token_balances):
            if len(token_balances[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(token_balances[chain_name])} tokens)\n"

            for token_data in token_balances[chain_name]:
                formatted_result += (
                    f"    Name: {token_data.name} | Balance (in usd): {token_data.balance_usd} $ "
                    f"| Amount: {token_data.amount} | CA: {token_data.contract_address}\n"
                )
            formatted_result += "\n"

    if debank_config.parse_nfts and len(nft_balances) > 0:
        total_nfts = sum(len(nfts) for nfts in nft_balances.values())
        formatted_result += f"\n========== NFT Balances ({total_nfts} nfts)\n"

        for chain_name in get_keys(nft_balances):
            if len(nft_balances[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(nft_balances[chain_name])} nfts)\n"

            for nft_data in nft_balances[chain_name]:
                formatted_result += (
                    f"    Name: {nft_data.name} | Price (in usd): {nft_data.balance_usd} $ "
                    f"| Amount: {nft_data.amount}\n"
                )
            formatted_result += "\n"

    if debank_config.parse_pools and len(pools_data) > 0:
        total_pools = sum(len(pool) for chain in pools_data.values() for pool in chain.values())
        formatted_result += f"\n========== Pool Balances ({total_pools} pools)\n"

        for chain_name in get_keys(pools_data):
            if len(pools_data[chain_name]) < 1:
                continue

            formatted_result += f"----- {chain_name.upper()} ({len(pools_data[chain_name])} pools)\n"

            for pool_name in get_keys(pools_data[chain_name]):
                if len(pools_data[chain_name][pool_name]) < 1:
                    continue

                formatted_result += f"===== {pool_name.upper()}\n"

                for pool_data in pools_data[chain_name][pool_name]:
                    formatted_result += (
                        f"    Name: {pool_data.name} | Balance (in usd): {pool_data.balance_usd} $ "
                        f"| Amount: {pool_data.amount}\n"
                    )
                formatted_result += "\n"

    formatted_result += "\n\n\n"

    return ResultFile(
        file_name=build_bucketed_result_file_name("debank", float(total_usd_balance)),
        content=formatted_result,
    )
