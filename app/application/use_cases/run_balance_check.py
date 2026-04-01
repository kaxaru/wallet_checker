from dataclasses import dataclass
from itertools import cycle

from app.application.services.account_processor import AccountProcessor
from app.domain.models import AccountJob, AccountProcessingResult
from app.domain.ports import AccountSource, BalanceProvider, ProxySource, ResultSink


@dataclass(frozen=True)
class RunBalanceCheckSummary:
    results: list[AccountProcessingResult]
    failures: list[str]
    total_balance: float
    account_count: int
    proxy_count: int


class RunBalanceCheckUseCase:
    def __init__(self, account_processor: AccountProcessor | None = None) -> None:
        self._account_processor = account_processor or AccountProcessor()

    def execute(
        self,
        *,
        account_source: AccountSource,
        proxy_source: ProxySource,
        result_sink: ResultSink,
        provider: BalanceProvider,
        threads: int,
    ) -> RunBalanceCheckSummary:
        accounts = account_source.load_accounts()
        proxies = proxy_source.load_proxies() or [None]
        jobs = [
            AccountJob(account=account, proxy=proxy)
            for account, proxy in zip(accounts, cycle(proxies))
        ]

        batch = self._account_processor.process(jobs, provider, threads)

        total_balance = 0.0
        for result in batch.results:
            result_sink.write(result)
            total_balance += result.total_balance

        return RunBalanceCheckSummary(
            results=batch.results,
            failures=batch.failures,
            total_balance=total_balance,
            account_count=len(accounts),
            proxy_count=len(proxies),
        )
