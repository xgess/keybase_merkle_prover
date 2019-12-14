
# Keybase-OpenTimestamps Merkle Root Prover

## What is this
fun for me
* A dockerized, AWS-Fargate deployable, Python Keybase chat bot
* Uses OpenTimestamps to create proofs so the Keybase servers cannot present different Merkle roots to different users (this would theoretically allow them to withhold information like Alice revoking a device). Keybase already does this, but I'm doing it in a different way with different tradeoffs.
* Publish these proofs right on Keybase using the bot's public channel (signed but not encrypted) so anyone can read them

## To whom is this useful
* Anyone who cares about the security guarantees provided by anchoring the entire Keybase ecosystem to the Bitcoin blockchain.
* Anyone interested in some example code for spinning up a Keybase chatbot in Python. Especially if you want to deploy it somewhere like AWS Fargate. 
* Anyone interested in some example code for using OpenTimestamps like it's an API, though admittedly I feel like there must be a better way to do this than I've done it. 

## Why
I really like that the Keybase security model includes pinning data to Bitcoin. It's an elegant solution to a very specific security issue (what if the Keybase servers collude with, for example, someone who has stolen your revoked device) that makes for a compelling, non-monetary use of the blockchain. Timestamping in general is cool, but anchoring the security of an application platform to guarantee no one is missing any updates they need is just :chef-kiss:. 

## the implementation
it's a dockerized python3.7 chatbot using [pykeybasebot](https://github.com/keybase/pykeybasebot). 
1. it uses pipfile locally and vanilla pip inside docker
2. username and paperkey for the bot are in env_file
3. the bot responds to any chat messages with a really long description of what it's doing.
4. i try to run everything through `make`. 

## setup
here's what you need to do:
* install pipenv, e.g. `brew install pipenv`
* make a keybase user and paperkey. put them in a new `./env_file` per the example.
* update `*.py` to your preferred bot logic.
* `make run` to spin it up locally. to spin it down, `make kill`.
* install [fargate cli](https://somanymachines.com/fargate/)
* go into your AWS console, find a security group and subnet, update `env_file`
* `make setup`
* `make deploy`

## If you're using this code for something else
Be careful with setting environment variables in Fargate. I'm doing them right on the `service create` step because this will only ever need `KEYBASE_USERNAME` and `KEYBASE_PAPERKEY`, but if I thought this thing would need more variables and that they might change, I'd be using `fargate service env set` which is quite a bit more work to wire up in a clean way with `make`. 


## TODO
* clean up the dockerfile to use official keybase one
* `make shell` should also log in the bot
* verify the sig over the root hash
* squash and push to github
* paginate the reading of messages so we aren't looking at every message every time
https://keybase.io/docs/server_security/merkle_root_in_bitcoin_blockchain
https://keybase.io/docs/server_security/our_merkle_key


