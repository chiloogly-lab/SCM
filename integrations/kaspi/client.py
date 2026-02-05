import time
import requests

KASPI_BASE_URL = "https://kaspi.kz/shop/api/v2"


class KaspiClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "X-Auth-Token": token,
            "Accept": "application/vnd.api+json",
            "User-Agent": "PostmanRuntime/7.51.1",
            "Connection": "keep-alive",
        })

    def get(self, path: str, params=None, timeout=20):
        url = f"https://kaspi.kz/shop/api/v2{path}"

        response = self.session.get(
            url,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()

        time.sleep(0.4)
        return response.json()
