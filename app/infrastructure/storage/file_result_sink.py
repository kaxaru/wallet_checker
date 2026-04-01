from pathlib import Path

from app.domain.models import AccountProcessingResult, ResultFile


class FileResultSink:
    def __init__(self, base_dir: str = "results") -> None:
        self._base_dir = Path(base_dir)

    def write(self, result: AccountProcessingResult) -> None:
        for file in result.files:
            self._append(file)

    def _append(self, file: ResultFile) -> None:
        target = self._base_dir / file.file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(file.content)

