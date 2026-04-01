from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from loguru import logger

from app.domain.models import AccountJob, AccountProcessingResult
from app.domain.ports import BalanceProvider


@dataclass(slots=True)
class AccountRunnerBatch:
    results: list[AccountProcessingResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


class ThreadPoolAccountRunner:
    def run(
        self,
        jobs: list[AccountJob],
        provider: BalanceProvider,
        max_workers: int,
    ) -> AccountRunnerBatch:

        if not jobs:
            return AccountRunnerBatch()

        ordered_results: list[AccountProcessingResult | None] = [None] * len(jobs)
        failures: list[str] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(provider.process, job): (index, job)
                for index, job in enumerate(jobs)
            }

            for future in as_completed(future_to_job):
                index, job = future_to_job[future]
                try:
                    ordered_results[index] = future.result()
                except Exception:
                    logger.exception("Failed to process account {}", job.account_address)
                    failures.append(job.account_address)

        return AccountRunnerBatch(
            results=[result for result in ordered_results if result is not None],
            failures=failures,
        )

