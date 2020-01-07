import asyncio
import logging
import os
import sys

from pykeybasebot import Bot

from interactivity import new_bot, start_bot
import last_success
from merkle_root import KEYBASE_MERKLE_ROOT_URL
from task import broadcast_new_root, update_messages


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s -- %(message)s',
)
NEW_ROOT_INTERVAL = 20 * 60  # every 20 minutes
ON_CHAIN_UPDATE_INTERVAL = 1 * 60  # every minute


################################

# loops for two-stage OTS proofs

async def new_proof_loop(bot: Bot):
    logger = logging.getLogger('new_proof')
    while True:
        logger.debug("ready to broadcast a new root")
        await broadcast_new_root(logger, bot)
        await asyncio.sleep(NEW_ROOT_INTERVAL)

async def update_proof_loop(bot: Bot):
    logger = logging.getLogger('update_proof')
    while True:
        logger.debug("+ loop starting")
        await update_messages(logger, bot)
        logger.debug(f"- loop complete - sleeping {ON_CHAIN_UPDATE_INTERVAL} seconds")
        await asyncio.sleep(ON_CHAIN_UPDATE_INTERVAL)

################################

# run everything
async def do_it():
    bot = new_bot()
    await asyncio.gather(
        start_bot(bot),
        new_proof_loop(bot),
        update_proof_loop(bot),
    )

asyncio.run(do_it())
