from app.domain.models import CheckerMode
from app.domain.ports import BalanceProvider


class CheckerRegistry:
    def __init__(self, providers: list[BalanceProvider] | None = None) -> None:
        self._providers: dict[CheckerMode, BalanceProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: BalanceProvider) -> None:
        self._providers[provider.checker_mode] = provider

    def get(self, checker_mode: CheckerMode) -> BalanceProvider:
        try:
            return self._providers[checker_mode]
        except KeyError as exc:
            raise ValueError(f"Checker provider is not registered: {checker_mode}") from exc
