from pathlib import Path

from app.domain.models import AccountProcessingResult, ResultFile


def build_bucketed_result_file_name(checker_name: str, total_balance: float) -> str:
    if 0 <= total_balance < 1:
        bucket = "0_1"
    elif 1 <= total_balance < 10:
        bucket = "1_10"
    elif 10 <= total_balance < 100:
        bucket = "10_100"
    elif 100 <= total_balance < 500:
        bucket = "100_500"
    elif 500 <= total_balance < 1000:
        bucket = "500_1000"
    else:
        bucket = "1000_plus"

    return f"{bucket}_{checker_name}.txt"


class ResultSink:
    def __init__(self, base_dir: str = "results") -> None:
        self.base_dir = Path(base_dir)

    def write(self, result: AccountProcessingResult) -> None:
        for file in result.files:
            self.append(file)

    def append(self, file: ResultFile) -> None:
        target = self.base_dir / file.file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(file.content)

