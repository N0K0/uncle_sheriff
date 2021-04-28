#!/bin/env python3
from typing import List

from structs import State, Block
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
    block_oldest: int = typer.Argument(
        OLDEST_BLOCK,
        help="What block to start the scan from",
    ),
    block_newest: int = typer.Argument(
        None,
        help="What block to end the scan on",
    ),
    gas_price_filter: int = typer.Argument(
        GAS_PRICE_FILTER,
        help="Max gas price for TXes we should monitor",
    ),
    ws_endpoint: str = typer.Argument(
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
        block_newest = w3.eth.block_number + 100

    if block_newest < 0:
        block_newest = w3.eth.block_number - abs(block_newest)

    print(f"Patrolling {block_oldest} to {block_newest}")

    # Lets start with finding all uncles in range.
    find_uncles(block_oldest, block_newest)

    # Filter out the relevant TXes from the DB
    start = database.lowest_fb_block()
    patrol_the_ranch(start, block_newest)


def patrol_the_ranch(block_oldest, block_newest):
    fb_txs = database.get_fb_tx(GAS_PRICE_FILTER)

    index = block_oldest


def find_uncles(
    block_oldest: int,
    block_newest: int,
):
    """
    Finds blocks in range,
    :param block_oldest:
    :param block_newest:
    :return:
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
    Traverse the blocks backwards untill we hit the oldest one. We will also add the "overflow" to the DB
    :param block_oldest: Lowest/Oldest block to stop at
    :param block_newest: Highest/Newest block to start the search at
    """
    index = block_newest
    while index > block_oldest:
        response = api.blocks(before=index, limit=SCAN_LIMIT)
        for block in reversed(response.blocks):
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
