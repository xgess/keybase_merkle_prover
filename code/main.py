import asyncio
import logging
import os
import sys

from pykeybasebot import Bot
import pykeybasebot.types.chat1 as chat1

import last_success
from merkle_root import KEYBASE_MERKLE_ROOT_URL
from task import broadcast_new_root, update_messages


logging.basicConfig(level=logging.DEBUG)
NEW_ROOT_INTERVAL = 60 * 60  # every hour
ON_CHAIN_UPDATE_INTERVAL = 1 * 60  # every 1 minute


################################

# setup the bot

async def handler(bot, event):
    if event.msg.content.type_name != chat1.MessageTypeStrings.TEXT.value:
        # not a basic chat message. bail.
        return
    if event.msg.sender.username == bot.username:
        # my own message in the channel. bail.
        return
    channel = event.msg.channel
    path = os.path.join(os.path.dirname(__file__), 'chat_response.txt')
    msg = f'{open(path).read()}'.format(**locals())
    await bot.chat.send(channel, msg)

    seqno = await last_success.fetch(bot)
    msg = f"And the last merkle root i've verified is this one: {KEYBASE_MERKLE_ROOT_URL}?seqno={seqno}"
    await bot.chat.send(channel, msg)

listen_options = {"hide-exploding": False, "filter_channels": None}

bot = Bot(
    username=os.environ["KEYBASE_USERNAME"],
    paperkey=os.environ["KEYBASE_PAPERKEY"],
    handler=handler,
)

################################

# loops for two-stage OTS proofs

async def new_proof_loop():
    while True:
        logging.debug("ready to broadcast a new root")
        await broadcast_new_root(bot)
        await asyncio.sleep(NEW_ROOT_INTERVAL)

async def update_proof_loop():
    while True:
        logging.debug("update messages | starting...")
        await update_messages(bot)
        logging.debug("update messages | sleeping...")
        await asyncio.sleep(ON_CHAIN_UPDATE_INTERVAL)

################################

# run everything
async def do_it():
    await asyncio.gather(
        bot.start(listen_options),
        new_proof_loop(),
        update_proof_loop(),
    )

asyncio.run(do_it())
