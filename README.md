
# python keybase docker bot

## What is this

### the usecase

### the implementation
it's a dockerized python3.7 chatbot using github.com/keybase/pykeybasebot. 
1. it uses pipfile locally and vanilla pip inside docker
2. username and paperkey for the bot are in env.sh
3. the bot has a noop handler, meaning it won't respond to any messages.
4. i try to run everything through `make`. 

## setup
here's what you need to do:
* get pipenv
* make a keybase user and paperkey. put them in an `env.sh`.
* update `run.py` to your preferred bot logic.
* `make run`


TODO
* fix error: "message edit of size 10933 bytes exceeds the maximum length of 10000 bytes". probably requires putting fewer things in each message :(
* add a loop that responds to any direct messages with an explanation of what this is and how to use it. maybe with some sample code. 
* add fargate deployment
* clean up the dockerfile to use official keybase one
* `make shell` should also log in the bot
* verify the sig over the root hash
https://keybase.io/docs/server_security/merkle_root_in_bitcoin_blockchain
https://keybase.io/docs/server_security/our_merkle_key


