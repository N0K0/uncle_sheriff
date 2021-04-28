from pymongo.mongo_client import MongoClient
from structs import Block, Transaction, BanditTransaction, saveable_dict
from typing import List, Optional

client = MongoClient(port=20001, username="root", password="rootpassword")
db = client["flashbots"]
fb_block = db["fb_block"]  # Saves all the FB blocks
bandit_tx = db["bandit"]  # Saves the suspected bandit blocks
fb_tx = db["fb_tx"]  # Saves all the fb tx

fb_block.create_index("block_number")
bandit_tx.create_index("transaction_hash")
fb_tx.create_index("transaction_hash")


def insert_block(block: Block):
    data = saveable_dict(block.dict())
    data["transactions"] = list(
        map(
            saveable_dict,
            data[
                "transactions",
            ],
        )
    )
    fb_block.replace_one(
        {"block_number": block.block_number},
        data,
        upsert=True,
    )


def insert_bandit(bandit: BanditTransaction):
    data = saveable_dict(bandit.dict())
    bandit_tx.replace_one(
        {"bandit_block": bandit.bandit_block},
        data,
        upsert=True,
    )


def insert_txs(txs: List[Transaction]):
    for tx in txs:
        d = saveable_dict(tx.dict())
        fb_tx.replace_one(
            {"transaction_hash": tx.transaction_hash},
            d,
            upsert=True,
        )


def lowest_fb_block() -> int:
    blocks = get_blocks()
    val = min([block.block_number for block in blocks])
    return val


def get_block(block_number: int) -> Optional[Block]:
    block = fb_block.find_one({"block_number": str(block_number)})
    if block:
        return Block(**block)
    return None


def get_blocks() -> List[Block]:
    result = fb_block.find({})
    result = list(map(lambda x: Block(**x), result))
    return result


def get_fb_tx(gas_filter: int):
    result = fb_tx.find({})
    result = map(lambda x: Transaction(**x), result)
    result = filter(lambda x: x.gas_price <= gas_filter, result)
    return list(result)
