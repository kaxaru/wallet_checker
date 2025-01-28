import json
import time
import logging
import requests
from utils.getFile import read_file

class CreateTaskResult:
    def __init__(self, error_id, task_id):
        self.error_id = error_id
        self.task_id = task_id


class GetTaskResultResponse:
    def __init__(self, error_id, status, solution):
        self.error_id = error_id
        self.status = status
        self.solution = solution


def create_task(private_key_hex: str, api_key: str) -> str:

    payload = {
        "clientKey": api_key,
                   "softId": 4759,
                    "task": {
                        "type": "RecaptchaV2TaskProxyless",
                        "websiteURL": "https://debank.com/",
                        "websiteKey": "6Lcw7ewpAAAAAPtZi4LTNCAWmWj-1h5ACTD_CQHE",
                        "minScore": 0.9
                    }
    }

    try:
        response = requests.post("https://api.2captcha.com/createTask", json=payload)
        response_data = response.json()

        if response_data.get('errorId') != 0:
            logging.error(f"{private_key_hex} | Ошибка в ответе при создании задачи: {response_data}")
            return None

        return str(response_data.get('taskId'))
    except Exception as e:
        logging.error(f"{private_key_hex} | Ошибка при отправке запроса на создание задачи: {e}")
        return None


def get_task_result(private_key_hex: str, task_id: str, api_key:str) -> str:
    payload = {
        "softId": 4759,
        "clientKey": api_key,
           "taskId": task_id
    }

    try:
        response = requests.post("https://api.2captcha.com/getTaskResult", json=payload)
        response_data = response.json()

        if response_data.get('errorId') != 0:
            logging.error(f"{private_key_hex} | Ошибка в ответе при получении результата задачи: {response_data}")
            return None

        if response_data["status"] == "ready":
            return response_data["solution"]["token"]

        logging.info(f"{private_key_hex} | Капча еще обрабатывается... Сплю 5 секунд.")
        time.sleep(5)
        return None
    except Exception as e:
        logging.error(f"{private_key_hex} | Ошибка при отправке запроса на получение результата задачи: {e}")
        return None


def solve_captcha(account: str) -> str:
    CONFIG_FILE = read_file("./data/config.json", is_json=True)
    api_key = CONFIG_FILE['2captcha_apikey']

    while True:
        task_id = create_task(account, api_key)
        if task_id is None:
            continue

        captcha_result = get_task_result(account, task_id, api_key)

        if captcha_result:
            return captcha_result