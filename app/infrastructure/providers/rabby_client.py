from app.domain.models import AccountJob, AccountProcessingResult, CheckerMode
from app.tasks.rabbyParser import parse_rabby_account


class RabbyBalanceProvider:
    checker_mode = CheckerMode.RABBY

    def process(self, job: AccountJob) -> AccountProcessingResult:
        return parse_rabby_account(job.as_task_input())

