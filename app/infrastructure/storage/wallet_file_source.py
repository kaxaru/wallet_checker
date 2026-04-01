from app.utils.getAccounts import get_all_wallets, get_main_wallet
from app.utils.getAddress import get_address


class AddressFileAccountSource:
    def load_accounts(self) -> list[object]:
        return get_address()


class WalletFileAccountSource:
    def load_accounts(self) -> list[object]:
        return get_all_wallets(get_main_wallet())

