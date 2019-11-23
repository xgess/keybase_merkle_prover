import asyncio
import logging
import os
import sys

import pykeybasebot.types.chat1 as chat1
from pykeybasebot import Bot
from task import do_the_thing


logging.basicConfig(level=logging.DEBUG)
INTERVAL = 5

# setup the bot
def noop_handler(*args, **kwargs):
    pass

bot = Bot(
    username=os.environ["KEYBASE_USERNAME"],
    paperkey=os.environ["KEYBASE_PAPERKEY"],
    handler=noop_handler,
)

# setup our loop
async def running_loop():
    while True:
        logging.debug("starting a run")
        await do_the_thing(bot)
        await asyncio.sleep(INTERVAL)

# run it!
asyncio.run(running_loop())
