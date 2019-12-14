
# Keybase-OpenTimestamps Merkle Root Prover

## What is this
fun for me
* A dockerized, AWS-Fargate deployable, Python Keybase chat bot
* Uses OpenTimestamps to create proofs so the Keybase servers cannot present different Merkle roots to different users (this would theoretically allow them to withhold information like Alice revoking a device). Keybase already does this (i.e. without OpenTimestamps), but I'm doing it in a different way with different tradeoffs.
* Publish these proofs right on Keybase using the bot's public channel (signed but not encrypted) so anyone can read them. 

## To whom is this useful
* Anyone who cares about the security guarantees provided by anchoring the entire Keybase ecosystem to the Bitcoin blockchain.
* Anyone interested in some example code for spinning up a Keybase chatbot in Python. Especially if you want to deploy it somewhere like AWS Fargate. 
* Anyone interested in some example code for using OpenTimestamps like it's an API, though admittedly I feel like there must be a better way to do this than I've done it. 

## Why
I really like that the Keybase security model includes pinning data to Bitcoin. It's an elegant solution to a very specific security issue (what if the Keybase servers collude with, for example, someone who has stolen your revoked device) that makes for a compelling, non-monetary use of the blockchain. Timestamping in general is neat, but anchoring the security of an application platform to guarantee no one is missing any updates they need is just :chef-kiss:. 

If my running bot is the only instance of anything posting these proofs, and if the Keybase servers know it's happening, then they could also withold these messages, which would admittedly defeat the purpose. On the other hand, if multiple people were running it, they would have a much harder time identifying all of them. Better yet, if you ran the bot inside a private team (i.e. all of the messages were sent to a channel that could only be read by team members), then the members of the team could check against the published proofs for their own private guarantee. 

## the implementation
it's a dockerized python3.7 chatbot using [pykeybasebot](https://github.com/keybase/pykeybasebot). 
1. it uses pipfile locally and vanilla pip inside docker
2. username and paperkey for the bot are in env_file
3. the bot responds to any chat messages with a really long description of what it's doing.
4. i try to run everything through `make`. 

## setup
*getting it running locally*:
* install pipenv, e.g. `brew install pipenv`
* make a keybase user and paperkey. you can do this through the CLI or GUI on some other device with keybase. you can also use a paperkey on your personal account to play around.
* update the env_file with your `KEYBASE_USERNAME` and `KEYBASE_PAPERKEY`.
```
cp ./env_file.example ./env_file
```
* If you're just using this as a skeleton, update `*.py` with your preferred logic.
* `make run` to spin it up locally. to spin it down, `make kill`.
* you can also run `make shell` to get a bash terminal inside the container with your keybase user logged in.

*to deploy it to AWS*:
* install [fargate cli](https://somanymachines.com/fargate/)
* go into your AWS console, find a security group and subnet, update `env_file`
* `make setup` will create all the things you need in AWS
* `make deploy` will push the artifacts and scale it up to 1 instance. 


## TODO
* i dunno. make a suggestion.

## Related Links
https://keybase.io/docs/server_security/merkle_root_in_bitcoin_blockchain
https://keybase.io/docs/server_security/our_merkle_key
