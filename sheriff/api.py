from typing import Optional, Union
from structs import Blocks, Transactions
import os

from requests.adapters import HTTPAdapter
from requests import Session
from urllib.parse import urljoin

flashbots_url = os.getenv("FLASHBOTS_API", "https://blocks.flashbots.net/v1/")


class ApiSession(Session):
    def __init__(self, prefix_url):
        super(ApiSession, self).__init__()

        adapter = HTTPAdapter(max_retries=10)
        self.mount("http://", adapter)
        self.mount("https://", adapter)
        self.prefix_url = prefix_url

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super(ApiSession, self).request(method, url, *args, **kwargs)


api = ApiSession(flashbots_url)


def blocks(
    block_number: Optional[str] = None,
    miner: Optional[str] = None,
    before: Optional[Union[int, str]] = None,  # Default to 'latest' server side
    limit: Optional[int] = None,  # Default to 100
):
    payload = {
        "block_number": block_number,
        "miner": miner,
        "before": before,
        "limit": limit,
    }

    resp = api.get(
        "blocks",
        params=payload,
    )
    return Blocks(**resp.json())


def transactions(
    before: Optional[int] = None,  # Default to 'latest server side'
    limit: Optional[int] = None,  # Default to 100
):
    payload = {"before": before, "limit": limit}
    resp = api.get("transactions", params=payload)
    return Transactions(**resp.json())
