
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
* make a keybase user and paperkey. put them in an `env.sh`.
* update `run.py` to your preferred bot logic.
* `make run`
