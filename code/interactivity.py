import asyncio
import logging
import os
import sys

from pykeybasebot import Bot
import pykeybasebot.types.chat1 as chat1

from async_helpers import retry_if_timeout
import last_success
from merkle_root import KEYBASE_MERKLE_ROOT_URL


async def bot_send(bot, channel, message):
    logger = logging.getLogger('bot_handler')
    return await retry_if_timeout(logger, bot.chat.send, channel, message)


async def handler(bot, event):
    logger = logging.getLogger('bot_handler')
    if event.msg.content.type_name != chat1.MessageTypeStrings.TEXT.value:
        # not a basic chat message. bail.
        return
    if event.msg.sender.username == bot.username:
        # my own message in the channel. bail.
        return
    channel = event.msg.channel
    body = event.msg.content.text.body
    sender = event.msg.sender.username
    is_admin = sender == os.environ["KEYBASE_OWNER"]

    command, *other_words = body.split(' ')
    message = ' '.join(other_words)
    if is_admin and (command == "!logsend"):
        await bot_send(bot, channel, f"sending your logs with message '{message}'...")
        await retry_if_timeout(logger, bot.logsend, message)
        await bot_send(bot, channel, "logs sent. thanks.")
    elif command == "!details":
        logger.debug(f"{channel.name} wants the full details")
        path = os.path.join(os.path.dirname(__file__), 'full_details.txt')
        msg = f'{open(path).read()}'.format(**locals())
        await bot_send(bot, channel, msg)

        seqno = await last_success.fetch(bot)
        msg = f"And the last merkle root i've verified is this one: {KEYBASE_MERKLE_ROOT_URL}?seqno={seqno}"
        await bot_send(bot, channel, msg)
    else:
        path = os.path.join(os.path.dirname(__file__), 'short_details.txt')
        msg = f'{open(path).read()}'.format(**locals())
        await bot_send(bot, channel, msg)


def new_bot() -> Bot:
    return Bot(
        username=os.environ["KEYBASE_USERNAME"],
        paperkey=os.environ["KEYBASE_PAPERKEY"],
        handler=handler,
    )

async def start_bot(bot: Bot):
    listen_options = {"hide-exploding": False, "filter_channels": None}
    admin_user = os.environ['KEYBASE_OWNER']
    admin_channel = chat1.ChatChannel(name=f"{admin_user},{bot.username}")
    await bot_send(bot, admin_channel, "starting up...")
    await bot.start(listen_options)
