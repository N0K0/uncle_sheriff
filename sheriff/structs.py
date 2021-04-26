from typing import List

from pydantic import BaseModel


class Transaction(BaseModel):
    transaction_hash: str
    tx_index: int
    block_number: int
    eoa_address: str
    to_address: str
    gas_used: int
    gas_price: str
    coinbase_transfer: str
    total_miner_reward: str


class Block(BaseModel):
    block_number: int
    miner: str
    miner_reward: str
    coinbase_transfers: str
    gas_used: int
    gas_price: str
    transactions: List[Transaction]


# Returned from the API
# https://blocks.flashbots.net/v1/blocks
class Blocks(BaseModel):
    latest_block_number: int
    blocks: List[Block]


# Returned from the API
# https://blocks.flashbots.net/v1/transactions
class Transactions(BaseModel):
    latest_block_number: int
    blocks: List[Transaction]
