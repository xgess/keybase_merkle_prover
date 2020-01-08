import asyncio
import logging
import os
import signal
import sys

from pykeybasebot import Bot

from interactivity import new_bot, start_bot, Seppuku
import last_success
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

# set up an event loop with graceful shutdown

loop = asyncio.get_event_loop()

async def shutdown(loop, signal=None):
    logging.info(f"received exit signal: {signal}")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    for task in tasks:
        task.cancel()

    logging.info("cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    logging.error(f"shutting down because of exception: {msg}")
    asyncio.create_task(shutdown(loop))

loop.set_exception_handler(handle_exception)

signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
for s in signals:
    loop.add_signal_handler(
        s, lambda s=s: asyncio.create_task(shutdown(loop, s)))


# add the tasks and start running
try:
    bot = new_bot(loop)
    logging.info(f"starting up an event loop for {bot.username}")
    tasks = asyncio.gather(
        start_bot(bot),
        new_proof_loop(bot),
        update_proof_loop(bot),
        return_exceptions=True,
    )
    loop.run_until_complete(tasks)
finally:
    logging.info("successfully shut down")
    loop.close()
