from app.domain.models import AccountJob, AccountProcessingResult, CheckerMode
from app.layer.debankType import ConfigStruct
from app.tasks.debankParser import parse_debank_account


class DebankBalanceProvider:
    checker_mode = CheckerMode.DEBANK

    def __init__(self, config: ConfigStruct) -> None:
        self._config = config

    def process(self, job: AccountJob) -> AccountProcessingResult:
        return parse_debank_account(job.as_task_input(), config=self._config)
