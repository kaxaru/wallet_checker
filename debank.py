import os
import json
import threading
from queue import Queue
from utils import  get_proxies, read_file, get_address, get_main_wallet, get_all_wallets
from tasks import parse_debank_account, debank_l2_balance_parser, parse_rabby_account

CONFIG_FILE = None


def input_user(prompt=""):
    return input(prompt).strip()


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def process_accounts(accounts, threads, user_action):

    def worker():
        while True:
            account = queue.get()
            if account is None:
                break

            try:
                if user_action == 1:
                    parse_debank_account(account)
                elif user_action == 2:
                    debank_l2_balance_parser(account)
                elif user_action == 3:
                    parse_rabby_account(account)
            finally:
                queue.task_done()

    queue = Queue()
    for account in accounts:
        queue.put(account)

    threads_list = []
    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.start()
        threads_list.append(t)

    queue.join()

    for _ in range(threads):
        queue.put(None)
    for t in threads_list:
        t.join()


def handle_panic():
    print("Unexpected Error occurred. Press Enter to exit..")
    input()
    exit(1)


def main():
    try:
        global CONFIG_FILE
        CONFIG_FILE = read_file("./data/config.json", is_json=True)

        proxies = get_proxies()

        ensure_dir("./results")

        # Чтение списка аккаунтов
        print("1. addresses \n2. mnemonic/etc")
        user_data = int(input_user("Enter Your Choice: "))
        if user_data not in {1, 2}:
            raise ValueError("Invalid User Action Number")

        if user_data == 1:
            account = get_address()
        else:
            account = get_main_wallet()
            account = get_all_wallets(account)
        print(f"Successfully Loaded {len(account)} Accounts // {len(proxies)} Proxies\n")

        use_multithreading = input("Enable multithreading? (y/n): ").lower() == 'y'
        threads = int(input("Number of threads: ")) if use_multithreading else 1

        if user_data == 1:
            print("1. Debank Checker\n2. Rabby Checker")
            user_action = int(input_user("Enter Your Choice: "))
            if user_action not in {1, 2}:
                raise ValueError("Invalid User Action Number")
            user_action = 3 if user_action == 2 else user_action
        else:
            print("1. Debank Checker\n2. Debank L2 Balance Parser\n3. Rabby Checker")
            user_action = int(input_user("Enter Your Choice: "))

            if user_action not in {1, 2, 3}:
                raise ValueError("Invalid User Action Number")

        print()

        process_accounts(list(zip(account, proxies)), threads, user_action)

        print("The Work Has Been Successfully Finished..\n")
        input("Press Enter to Exit..")
    except Exception as e:
        print(f"Error: {e}")
        handle_panic()


if __name__ == "__main__":
    main()