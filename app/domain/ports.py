from typing import Protocol, runtime_checkable
from app.domain.models import AccountJob, AccountProcessingResult, CheckerMode


@runtime_checkable
class BalanceProvider(Protocol):
    checker_mode: CheckerMode

    def process(self, job: AccountJob) -> AccountProcessingResult:
        ...

@runtime_checkable
class AccountSource(Protocol):
    def load_accounts(self) -> list[object]:
        ...

@runtime_checkable
class ProxySource(Protocol):
    def load_proxies(self) -> list[dict[str, str] | None]:
        ...

@runtime_checkable
class ResultSink(Protocol):
    def write(self, result: AccountProcessingResult) -> None:
        ...

@runtime_checkable
class CaptchaSolver(Protocol):
    def solve(self, account_address: str, api_key: str) -> str:
        ...

