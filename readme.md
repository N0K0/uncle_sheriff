# The uncle sheriff 🤠

## Goal of this project

What we are trying to do is find miners which are using 0 gasPrice transactions from uncles for their own MEV.
Read:

* https://medium.com/alchemy-api/unmasking-the-ethereum-uncle-bandit-a2b3eb694019
* https://twitter.com/bertcmiller/status/1382673587715342339

## Running the project

```bash
#Setup mongodb and mongo express
docker-compose up

# project setup with poetry (python pkg manager)
poetry install

python sheriff/runner.py  --help

```

## The steps are simple enough:

1) Fetch all Flashbots mev blocks from the block.flashbots.net api
1) Find all Flashbots bundle TXes that ended up in an uncle
1) Find all Flashbots bundle TXes that was then later used in the main chain.
1) Filter on TXes which has gasPrice 0
1) Filter on TXes which are out of gasPrice order *TODO*
1) Output into a reasonable format *TODO*


### Fetch all Flashbots mev blocks from the block.flashbots.net api
Simple enough. The API is awesome and nice.
https://blocks.flashbots.net/

### Fetch all flashbots uncles from geth
Go through all flashbots blocks, check if the block became an uncle
From uncle: Save all bundle TXes with gas_price under `--gas-price-filter`

Keep TXes in database until EOA is reused (aka nonce increased) *TODO*

If we find a TX in another block we report:
Uncle block number, Bandit block number, tx detected

Also report on other invalidation via EoA reused

## Things to figure out:

When can we reasonably discard a Flashbots TX from our cache?
* We can check the from address and figure out if the TX nonce has been used for another tx?
  Let's try by checking the if the EOA has been used again, and not for the same TX

What other sources are there for false positives?
* The user may have resent the same bundle, need to find out how to check for this. 
  Possible to just concat the different tx hashes and use that as an key?
  
* Why is 12237616 missing from the API?
  
## Notes/Scratch
https://github.com/flashbots/mev-blocks/blob/master/scripts/fetch_block_profits.py
