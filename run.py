import asyncio
import logging
import os
import sys

from pykeybasebot import Bot

from task import broadcast_new_root, update_messages


logging.basicConfig(level=logging.DEBUG)
NEW_ROOT_INTERVAL = 60 * 60  # every hour
ON_CHAIN_UPDATE_INTERVAL = 1 * 60  # every 1 minute


# setup the bot
def noop_handler(*args, **kwargs):
    pass

bot = Bot(
    username=os.environ["KEYBASE_USERNAME"],
    paperkey=os.environ["KEYBASE_PAPERKEY"],
    handler=noop_handler,
)

# loops for tasks
async def post_new_roots():
    while True:
        logging.debug("ready to broadcast a new root")
        await broadcast_new_root(bot)
        await asyncio.sleep(NEW_ROOT_INTERVAL)


async def update_on_chain():
    while True:
        logging.debug("ready to update some messages")
        await update_messages(bot)
        await asyncio.sleep(ON_CHAIN_UPDATE_INTERVAL)


# start the runner
async def do_it():
  await asyncio.gather(post_new_roots(), update_on_chain())

# run it!
asyncio.run(do_it())
