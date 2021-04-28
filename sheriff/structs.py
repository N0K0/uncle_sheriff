from typing import List

from pydantic import BaseModel


def saveable_dict(d: dict) -> dict:
    """
    Converts sets to lists
    Converts ints to str
    """
    for o in d.items():
        k, v = o
        if isinstance(v, int):
            d[k] = str(v)
        elif isinstance(v, set):
            d[k] = list(v)
        elif isinstance(v, dict):
            d[k] = saveable_dict(v)
    return d.copy()


class Transaction(BaseModel):
    # API data
    transaction_hash: str
    tx_index: int
    block_number: int
    eoa_address: str
    to_address: str
    gas_used: int
    gas_price: int
    coinbase_transfer: int
    total_miner_reward: int


class Block(BaseModel):
    # API data
    block_number: int
    miner: str
    miner_reward: int
    coinbase_transfers: int
    gas_used: int
    gas_price: int
    transactions: List[Transaction]


# Returned from the API
# https://blocks.flashbots.net/v1/blocks
class Blocks(BaseModel):
    # API data
    latest_block_number: int
    blocks: List[Block]


# Returned from the API
# https://blocks.flashbots.net/v1/transactions
class Transactions(BaseModel):
    latest_block_number: int
    blocks: List[Transaction]


class BanditTransaction(BaseModel):
    transaction_hash: str
    bandit_block: int
    origin_block: int


# Model used to persis data between runs
class State(BaseModel):
    flashbots_last_block: int  # Last flashbots block scanned
    geth_last_block: int  # Last Main net block scanned for TX

    fb_uncle_blocks: List[Block]  # Might be nice to have for faster checking
    fb_uncle_tx: List[Transaction]

    bandit_tx: List[BanditTransaction]

    search_oldest: int
    search_newest: int
