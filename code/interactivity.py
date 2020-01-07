import asyncio
import logging
import os
import sys

from pykeybasebot import Bot
import pykeybasebot.types.chat1 as chat1


async def handler(bot, event):
    logger = logging.getLogger('bot_handler')
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
    logger.debug(f"sent a response message in {channel.name}")


def new_bot() -> Bot:
    return Bot(
        username=os.environ["KEYBASE_USERNAME"],
        paperkey=os.environ["KEYBASE_PAPERKEY"],
        handler=handler,
    )

async def start_bot(bot: Bot):
    listen_options = {"hide-exploding": False, "filter_channels": None}
    await bot.start(listen_options)
