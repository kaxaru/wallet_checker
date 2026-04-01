from pathlib import Path

from app.utils.getFile import read_file

ADDRESS_FILE = Path("wallets/address.txt")


def get_address() -> list[str]:
    return read_file(str(ADDRESS_FILE), check_empty=False)
