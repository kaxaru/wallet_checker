from app.domain.models import AccountJob
from app.domain.ports import BalanceProvider

from .thread_pool_runner import AccountRunnerBatch, ThreadPoolAccountRunner

AccountProcessorBatch = AccountRunnerBatch


class AccountProcessor:
    def __init__(self, runner: ThreadPoolAccountRunner | None = None) -> None:
        self._runner = runner or ThreadPoolAccountRunner()

    def process(
        self,
        jobs: list[AccountJob],
        provider: BalanceProvider,
        threads: int,
    ) -> AccountProcessorBatch:
        return self._runner.run(jobs, provider, max_workers=threads)
