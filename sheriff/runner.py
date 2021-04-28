#!/bin/env python3
from typing import List

from structs import State, Block, Transaction, BanditTransaction
from web3 import Web3, WebsocketProvider
import api
import database
import typer
from tqdm import tqdm

GAS_PRICE_FILTER = 0
OLDEST_BLOCK = 11834049  # Actual oldest is 11550019, but api does not have it
SCAN_LIMIT = 10000

w3: Web3 = Web3()


def ride_your_horse_down_town(
    block_oldest: int = typer.Option(
        OLDEST_BLOCK,
        help="What block to start the scan from",
    ),
    block_newest: int = typer.Option(
        None,
        help="What block to end the scan on",
    ),
    gas_price_filter: int = typer.Option(
        GAS_PRICE_FILTER,
        help="Max gas price for TXes we should monitor",
    ),
    ws_endpoint: str = typer.Option(
        "ws://localhost:8546", help="Which WS endpoint we are going to use"
    ),
):
    global w3
    global GAS_PRICE_FILTER
    GAS_PRICE_FILTER = gas_price_filter
    w3 = Web3(WebsocketProvider(ws_endpoint))

    if block_oldest < 0:
        block_oldest = w3.eth.block_number - abs(block_oldest)

    # TODO: Make none activate a live mode instead of stopping
    if block_newest is None:
        block_newest = w3.eth.block_number

    if block_newest < 0:
        block_newest = w3.eth.block_number - abs(block_newest)

    print(f"Patrolling {block_oldest} to {block_newest}")

    # Lets start with finding all uncles in range.
    find_uncles(block_oldest, block_newest)

    # Filter out the relevant TXes from the DB
    start = max(database.lowest_fb_block(), block_oldest)
    patrol_the_ranch(start, block_newest)


def patrol_the_ranch(block_oldest, block_newest):
    global w3
    pending_tx: List[Transaction] = []

    for index in range(block_oldest, block_newest):
        print(f"Index: {index}")

        # TODO: Check if FB_TX is in block
        geth_block = w3.eth.get_block(index, full_transactions=True)
        geth_tx = geth_block["transactions"]
        for tx in geth_tx:
            for fb_tx in pending_tx:
                if tx["hash"].hex() == fb_tx.transaction_hash:
                    print("Found something!")
                    print(tx)
                    print(fb_tx)
                    database.insert_bandit(
                        BanditTransaction(
                            transaction_hash=tx["hash"].hex(),
                            bandit_block=index,
                            origin_block=fb_tx.block_number,
                        )
                    )

        # TODO: Check if EOA is reused, may prune retries++

        # Add new TXes in the end, since we don't want them while testing the rest of the block
        if fb_block := database.get_block(index):
            print("FB block, adding TX to scan")
            pending_tx.extend(fb_block.transactions)


def find_uncles(
    block_oldest: int,
    block_newest: int,
):
    """
    Finds uncle blocks in range,
    """
    global w3

    blocks: List[Block] = database.get_blocks()

    if len(blocks) == 0:
        get_blocks_in_range(block_oldest, block_newest)
    else:
        numbers = [item.block_number for item in blocks]
        db_block_oldest = min(numbers)
        db_block_newest = max(numbers)
        get_blocks_in_range(block_oldest, db_block_oldest)
        get_blocks_in_range(db_block_newest, block_newest)


def get_blocks_in_range(block_oldest, block_newest) -> None:
    """
    Traverse the blocks backwards until we hit the oldest one. We will also add the "overflow" to the DB
    :param block_oldest: Lowest/Oldest block to stop at
    :param block_newest: Highest/Newest block to start the search at
    """
    index = block_newest
    while index > block_oldest:

        if (index - SCAN_LIMIT) < block_oldest:
            limit = index - block_oldest
        else:
            limit = SCAN_LIMIT

        response = api.blocks(before=index, limit=limit)
        for block in response.blocks:
            if check_if_uncle(block.block_number):
                print(f"Uncle: {block.block_number}")
                database.insert_block(block)
                database.insert_txs(block.transactions)

        if len(response.blocks) == 0:
            # No results -> We are done
            return
        else:
            # The FB api response is always sorted.
            index = response.blocks[-1].block_number


# TODO: Is there an actual correct way to do this other than reading all the way to latest?
def check_if_uncle(block_num: int, distance=5) -> bool:
    """
    Naive uncle check. Looks at the next `distance` number of block to check for back reference
    :param block_num: Block which we are checking
    :param distance: number of blocks to check
    :return: bool
    """
    global w3
    for block in range(block_num + 1, block_num + distance):
        for index in range(w3.eth.get_uncle_count(block)):
            unc_block = w3.eth.get_uncle_by_block(block, index)
            if block_num == int(unc_block["number"], 16):
                return True
    return False


if __name__ == "__main__":
    typer.run(ride_your_horse_down_town)
