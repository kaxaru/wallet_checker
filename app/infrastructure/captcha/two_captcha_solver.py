from app.utils.captcha_solver import solve_captcha


class TwoCaptchaSolver:
    def solve(self, account_address: str, api_key: str) -> str:
        return solve_captcha(account_address, api_key)

