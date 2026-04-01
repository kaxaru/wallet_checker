from app.domain.models import AccountJob, AccountProcessingResult, CheckerMode
from app.domain.ports import CaptchaSolver
from app.layer.debankType import ConfigStruct
from app.tasks.debankL2Parser import debank_l2_balance_parser


class DebankL2BalanceProvider:
    checker_mode = CheckerMode.DEBANK_L2

    def __init__(self, config: ConfigStruct, captcha_solver: CaptchaSolver) -> None:
        self._config = config
        self._captcha_solver = captcha_solver

    def process(self, job: AccountJob) -> AccountProcessingResult:
        return debank_l2_balance_parser(
            job.as_task_input(),
            config=self._config,
            captcha_solver=self._captcha_solver.solve,
        )
