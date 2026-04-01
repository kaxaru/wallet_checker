from collections.abc import Callable
from enum import Enum
from pathlib import Path
import sys
from dataclasses import dataclass
from typing import TypeVar

from loguru import logger

from app.application.services.checker_registry import CheckerRegistry
from app.application.use_cases.run_balance_check import RunBalanceCheckUseCase
from app.domain.models import AccountInputMode, CheckerMode, MenuOption
from app.domain.ports import AccountSource, ProxySource, ResultSink
from app.infrastructure.captcha.two_captcha_solver import TwoCaptchaSolver
from app.infrastructure.providers.debank_client import DebankBalanceProvider
from app.infrastructure.providers.debank_l2_client import DebankL2BalanceProvider
from app.infrastructure.providers.rabby_client import RabbyBalanceProvider
from app.infrastructure.storage.file_result_sink import FileResultSink
from app.infrastructure.storage.proxy_file_source import FileProxySource
from app.infrastructure.storage.wallet_file_source import (
    AddressFileAccountSource,
    WalletFileAccountSource,
)
from app.layer.debankType import ConfigStruct
from app.utils.getFile import read_file

DEFAULT_CONFIG_PATH = Path("data/config.json")
DEFAULT_RESULTS_DIR = Path("results")
TOption = TypeVar("TOption", bound=Enum)


@dataclass(frozen=True)
class RuntimeSettings:
    checker_registry: CheckerRegistry
    proxy_source: ProxySource
    result_sink: ResultSink
    run_balance_check_use_case: RunBalanceCheckUseCase


ACCOUNT_INPUT_OPTIONS: tuple[MenuOption[AccountInputMode], ...] = (
    MenuOption("1", "Addresses", AccountInputMode.ADDRESSES),
    MenuOption("2", "Mnemonic / Private key", AccountInputMode.WALLETS),
)

ADDRESS_CHECKER_OPTIONS: tuple[MenuOption[CheckerMode], ...] = (
    MenuOption("1", "Debank Checker", CheckerMode.DEBANK),
    MenuOption("2", "Rabby Checker", CheckerMode.RABBY),
)

WALLET_CHECKER_OPTIONS: tuple[MenuOption[CheckerMode], ...] = (
    MenuOption("1", "Debank Checker", CheckerMode.DEBANK),
    MenuOption("2", "Debank L2 Balance Parser", CheckerMode.DEBANK_L2),
    MenuOption("3", "Rabby Checker", CheckerMode.RABBY),
)


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    )


def load_runtime_settings(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    results_dir: str | Path = DEFAULT_RESULTS_DIR,
) -> RuntimeSettings:
    config = ConfigStruct(**read_file(str(config_path), is_json=True))
    captcha_solver = TwoCaptchaSolver()
    checker_registry = CheckerRegistry(
        [
            DebankBalanceProvider(config),
            DebankL2BalanceProvider(config, captcha_solver),
            RabbyBalanceProvider(),
        ]
    )

    return RuntimeSettings(
        checker_registry=checker_registry,
        proxy_source=FileProxySource(config.proxy_format),
        result_sink=FileResultSink(str(results_dir)),
        run_balance_check_use_case=RunBalanceCheckUseCase(),
    )


def select_option(
    title: str,
    options: tuple[MenuOption[TOption], ...],
    input_func: Callable[[str], str],
) -> TOption:
    menu_text = "\n".join([title, *[f"{option.key}. {option.label}" for option in options]])
    logger.info("\n{}", menu_text)

    selected_key = input_func("Enter Your Choice: ")
    option_map = {option.key: option.value for option in options}
    try:
        return option_map[selected_key]
    except KeyError as exc:
        raise ValueError(f"Invalid choice: {selected_key}") from exc


def get_checker_options(input_mode: AccountInputMode) -> tuple[MenuOption[CheckerMode], ...]:
    if input_mode is AccountInputMode.ADDRESSES:
        return ADDRESS_CHECKER_OPTIONS
    return WALLET_CHECKER_OPTIONS


def get_account_source(input_mode: AccountInputMode) -> AccountSource:
    if input_mode is AccountInputMode.ADDRESSES:
        return AddressFileAccountSource()
    return WalletFileAccountSource()
