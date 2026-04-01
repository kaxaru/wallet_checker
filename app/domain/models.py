from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

TEnum = TypeVar("TEnum", bound=Enum)


class AccountInputMode(Enum):
    ADDRESSES = "addresses"
    WALLETS = "wallets"


class CheckerMode(Enum):
    DEBANK = "debank"
    DEBANK_L2 = "debank_l2"
    RABBY = "rabby"


@dataclass(frozen=True)
class MenuOption(Generic[TEnum]):
    key: str
    label: str
    value: TEnum


@dataclass(slots=True)
class ResultFile:
    file_name: str
    content: str


@dataclass(slots=True)
class AccountProcessingResult:
    account_address: str
    total_balance: float
    files: list[ResultFile] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AccountJob:
    account: Any
    proxy: dict[str, str] | None = None

    @property
    def account_address(self) -> str:
        if isinstance(self.account, dict) and "wallet" in self.account:
            return self.account["wallet"].address
        return self.account.strip()

    def as_task_input(self) -> tuple[Any, dict[str, str] | None]:
        return self.account, self.proxy
