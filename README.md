
# Keybase-OpenTimestamps Merkle Root Prover

## What is this
a fun (for me) combo of a few of my favorite things.
* A dockerized, AWS-Fargate deployable, Python Keybase chat bot
* Uses OpenTimestamps to create proofs so the Keybase servers cannot present different merkle roots to different users (this would theoretically allow them to withhold information like Alice revoking a device). Keybase already does this (i.e. without OpenTimestamps), but I'm doing it in a different way with different tradeoffs.
* Publish these proofs right on Keybase using the bot's public channel (signed but not encrypted) so anyone can read them. 


## To whom is this useful
* Anyone who cares about the security guarantees provided by anchoring the entire Keybase ecosystem to the Bitcoin blockchain.
* Anyone interested in some example code for spinning up a Keybase chatbot in Python. Especially if you want to deploy it somewhere like AWS Fargate. I'm also using keybase's encrypted key-value store (just for keeping track of the latest successfully verified root), which I think is really neat. 
* Anyone interested in some example code for using OpenTimestamps like it's an API, though admittedly I feel like there must be a better way to do this than I've done it (shelling out to a subprocess). 


## Why
I really like that the Keybase security model includes pinning data to Bitcoin. It's an elegant solution to a very specific security issue (what if the Keybase servers collude with, for example, someone who has stolen your recently revoked device) that makes for a compelling, non-monetary use of the blockchain. Timestamping in general is interesting, but anchoring the security of an application platform to guarantee no one is missing any updates they need is just 
![chef kiss](https://is1-ssl.mzstatic.com/image/thumb/Purple128/v4/81/08/9e/81089ec4-c468-ace0-02bb-01c65e753c89/source/512x512bb.jpg)


If my running bot is the only instance of anything posting these proofs, and if the Keybase servers know it's happening, then they could just withhold these messages from you, which would admittedly defeat the purpose. On the other hand, if multiple people were running it, they would have a harder time identifying all of them. Better yet, if you ran the bot inside a private team (i.e. all of the messages were sent to a channel that could only be read by team members), then the members of the team could check against the published proofs for their own private guarantee. 


## Implementation
#### What it's doing
1. Every *SOME_TIME_INTERVAL* (currently 1 hour but I reserve the right to change this without updating here), the running bot will fetch from Keybase the latest [merkle root](https://keybase.io/_/api/1.0/merkle/root.json) which comes with a bunch of other details: a seqno so this specific root can be fetched again deterministically, skip sequences to help validation go faster, sub-components that each have payloads, a PGP signature, ...
2. I'm doing a whole bunch of validation: 
  * that the PGP signature is valid for Keybase's published key, 
  * that the subject of the signature matches the payload, 
  * that the actual merkle root matches, 
  * ... 
4. Now that we know the PGP message is good, take a sha512 hash of it. do an `ots stamp` with those bytes. This creates a "preliminary" timestamp proof, and submits it to a bunch of calendar servers. It's not actually in the Bitcoin blockchain yet though. 
5. Compose some JSON with: 
  * base64 encoded data that we submitted to OpenTimestamps, 
  * base64 encoded data that we got back from OpenTimestamps, 
  * the actual, global merkle root, 
  * the seqno of this root, which we can use to fetch it deterministically in the future, 
  * a status field so we can track whether or not the OTS proof has made it to the blockchain (`PRELIMINARY` or `VERIFIABLE`)
  * some other metadata that's not relevant for a simple readme. 
6. Publish the JSON to my public channel (with `PRELIMINARY` status) so everyone in the world can read it.
7. Periodically pull back all of my recently published, `PRELIMINARY` messages.
8. Try to `ots upgrade` them. If it works (i.e. the OTS proof has made it to the blockchain), edit the keybase message's JSON to have the new OTS proof, and change the status to `VERIFIABLE`.

#### BuiltWith
it's a dockerized python3 chatbot using [pykeybasebot](https://github.com/keybase/pykeybasebot). 
1. it uses pipfile locally and vanilla pip inside docker. async and await. a teeny bit of typing (i really should do more)
2. username and paperkey for the bot are in env_file
3. the bot responds to any chat messages with a really long description of what it's doing.
4. i try to run everything through `make`, so if you're wondering how something works, I suggest starting there.


## Setup
#### Locally:
* install pipenv, e.g. `brew install pipenv`
* make a keybase user and paperkey. you can do this through the CLI or GUI on some other device with keybase. you can also just use a paperkey and your personal account.
* update the env_file with your `KEYBASE_USERNAME` and `KEYBASE_PAPERKEY`.
```
cp ./env_file.example ./env_file
```
* If you're just using this as a skeleton, update `code/*.py` with your preferred logic.
* `make run` to spin it up locally. to spin it down, `make kill`.
* you can also run `make shell` to get a bash terminal inside the container with your keybase user logged in.
* if you broadcasted a bunch of public messages and you're ready to wipe the slate clean, you can do that inside the docker container (i.e. after running `make shell`) by running `keybase chat delete-history $KEYBASE_USERNAME --public`

#### Deployed:
* install [fargate cli](https://somanymachines.com/fargate/)
* go into your AWS console, find a security group and subnet (follow the docs for the fargate cli for what these need to look like), and update your `env_file`. You probably also need `~/.aws`. honestly just look at the fargate cli stuff. 
* running `make setup` will create everything you need in AWS
* running `make deploy` will push the artifacts and scale it up to 1 running instance.


## Verifying
If you want to verify my work (which would be great), I definitely recommend skimming my code to make sure it's doing what you think, especially all the PGP and hashing stuff (which is in `merkle_root.py`).
If you're going to use the `ots` CLI to see those proofs in action, first of all don't bother unless the `status` is `VERIFIABLE`. You'll need to get the raw bytes (it's currently base64 encoded) from a couple of the fields into files in the same directory. If you have a Bitcoin node running locally, then it would look something like this:
```
> cat one_of_my_posts | jq -r .root.b64stamped | base64 --decode > ./sig_hash.dat
> cat one_of_my_posts | jq -r .ots | base64 --decode > ./sig_hash.dat.ots
> ots verify kb_sig.dat.ots
```
If you aren't running Bitcoin on this machine and you don't want to wire up an RPC connection, you could do this instead of the full `verify`:
```
> ots --no-bitcoin verify sig_hash.dat.ots
> ots info sig_hash.dat.ots
```
And you'll see the Merkle path and block height.


## Related Links
* [OpenTimestamps](https://github.com/opentimestamps/opentimestamps-client/blob/master/README.md)
* [keybase merkle root basics](https://keybase.io/docs/server_security/our_merkle_key)
* [keybase merkle root in bitcoin](https://keybase.io/docs/server_security/merkle_root_in_bitcoin_blockchain)


## TODO
* i dunno. make a suggestion.
