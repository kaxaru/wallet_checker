from loguru import logger
from typing import NoReturn

from app.application.use_cases.run_balance_check import RunBalanceCheckSummary
from app.utils.exceptions import ApplicationError
from configure import (
    ACCOUNT_INPUT_OPTIONS,
    configure_logging,
    get_account_source,
    get_checker_options,
    load_runtime_settings,
    select_option,
)

def input_user(prompt: str) -> str:
    return input(prompt).strip()

def input_thread_count() -> int:
    use_multithreading = input_user("\nEnable multithreading? (y/n): ").lower()
    if use_multithreading in {"y", "yes", "ok"}:
        threads = int(input_user("Number of threads: "))
        return threads

    return 1

def log_summary(summary: RunBalanceCheckSummary) -> None:
    logger.info(
        f"Successfully loaded {summary.account_count} accounts // {summary.proxy_count} proxies",
    )
    for result in summary.results:
        logger.info(
            f"\naccount -> {result.account_address}, balance -> {result.total_balance}"
        )

    logger.info(
        f"Total balance on accounts -> {summary.total_balance}"
    )
    logger.info(
        f"Successfully processed {len(summary.results)} of {summary.account_count} accounts",
    )
    if summary.failures:
        logger.warning(
            "Failed accounts ({}): {}",
            len(summary.failures),
            ", ".join(summary.failures),
        )


def exit_with_prompt(message: str, exit_code: int = 1) -> NoReturn:
    logger.info(message)
    input()
    raise SystemExit(exit_code)


def main() -> None:
    try:
        configure_logging()
        runtime = load_runtime_settings()
        input_mode = select_option("Account source", ACCOUNT_INPUT_OPTIONS, input_user)
        account_source = get_account_source(input_mode)
        threads = input_thread_count()
        checker_mode = select_option(
            "Checker mode",
            get_checker_options(input_mode),
            input_user,
        )
        provider = runtime.checker_registry.get(checker_mode)

        summary = runtime.run_balance_check_use_case.execute(
            account_source=account_source,
            proxy_source=runtime.proxy_source,
            result_sink=runtime.result_sink,
            provider=provider,
            threads=threads,
        )
        log_summary(summary)
        logger.info("The work has been successfully finished")
        input("Press Enter to Exit..")
    except ApplicationError as exc:
        logger.error("{}", exc)
        exit_with_prompt("Application error occurred. Press Enter to exit..")
    except Exception:
        logger.exception("Fatal error")
        exit_with_prompt("Unexpected error occurred. Press Enter to exit..")


if __name__ == '__main__':
    main()
