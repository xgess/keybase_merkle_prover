import asyncio
from base64 import b64decode, b64encode
from dataclasses import dataclass, field, replace
from dataclasses_json import dataclass_json
from enum import Enum
import json
import logging
from typing import List

import pykeybasebot.types.chat1 as chat1

import kb_ots
import last_success
from merkle_root import fetch_keybase_merkle_root, MerkleRoot


class StampStatus(Enum):
    PRELIMINARY = "PRELIMINARY"
    VERIFIABLE = "VERIFIABLE"


@dataclass_json
@dataclass
class StampedMerkleRoot:
    # this is the object that gets serialized into a broadcasted keybase chat msg
    root: MerkleRoot
    ots: str = ""  # base64 encoded string of the bytes in the `.ots` file
    version: int = 0
    status: StampStatus = StampStatus.PRELIMINARY


async def broadcast_new_root(logger, bot):
    merkle_root = fetch_keybase_merkle_root()
    logger.debug(f"fetched and validated {merkle_root.seqno}")
    try:
        ots = await kb_ots.stamp(merkle_root.data_to_stamp)
    except kb_ots.StampError as e:
        logger.error(f"error stamping {merkle_root.seqno}: {e}")
        return

    stamped_root = StampedMerkleRoot(
        version=0,
        root=merkle_root,
        ots=ots,
        status=StampStatus.PRELIMINARY,
    )

    my_public_channel = chat1.ChatChannel(name=bot.username, public=True)
    res = await retry_if_timeout(logger, bot.chat.send, my_public_channel, stamped_root.to_json())
    logger.info(f"broadcasted {merkle_root.seqno} at msg_id {res.message_id}")


async def retry_if_timeout(logger, func, *args, **kwargs):
    for i in range(0,100):
        try:
            result = await func(*args, **kwargs)
        except asyncio.TimeoutError:
            logger.error(f"got a timeout error on attempt {i+1}. retrying...")
            await asyncio.sleep(0.5)
            continue
        break
    else:
        raise asyncio.TimeoutError("retries exhausted :(")
    return result


async def update_messages(logger, bot):
    channel = chat1.ChatChannel(name=bot.username, public=True)
    # TODO: paginate this more intelligently. I think Keybase will automatically
    # give the most recent 100 messages, which is probably fine to be honest.
    all_posts = await retry_if_timeout(logger, bot.chat.read, channel)
    for m in reversed(all_posts):
        msg_id = m.id
        body = ""
        try:
            content_type = m.content.type_name
            if content_type not in ('edit', 'text'):
                # e.g. a `deletehistory`
                logger.debug(f"message {msg_id} is a {content_type} - skip")
                continue
            stamped_root = StampedMerkleRoot.from_json((m.content.text or m.content.edit).body)
        except Exception as e:
            # any errors in here we should probably fix
            logger.error(f"message {msg_id} doesn't parse as a stamped root ({e}) - skip - {m}")
            continue
        if stamped_root.version != 0:
            logger.debug(f"message {msg_id} has an old version - skip")
            continue
        if stamped_root.status is StampStatus.VERIFIABLE:
            logger.debug(f"message {msg_id} is already verifiable - skip")
        elif stamped_root.status is StampStatus.PRELIMINARY:
            await update_ots_for_msg(logger, bot, msg_id, stamped_root)
            await asyncio.sleep(1)  # necessary for broadcasting to succeed :/
        else:
            logger.error(f"message {m.id} does not have a valid status: {stamped_root}")


async def update_ots_for_msg(logger, bot, msg_id, stamped_root):
    seqno = stamped_root.root.seqno
    ots_data = b64decode(stamped_root.ots)

    try:
        completed_ots = await kb_ots.upgrade(
            identifier=msg_id,
            raw_data=stamped_root.root.data_to_stamp,
            ots_data=ots_data,
        )
    except (kb_ots.VerifyError, kb_ots.UpgradeError) as e:
        logger.info(f"message {msg_id} is not yet ready: {e}")
        return

    verifiable_stamp = replace(stamped_root,
        status=StampStatus.VERIFIABLE,
        ots=completed_ots,
    )
    channel = chat1.ChatChannel(name=bot.username, public=True)

    # edit the message with the new deets
    seqno = verifiable_stamp.root.seqno
    try:
        res = await retry_if_timeout(logger, bot.chat.edit, channel, msg_id, verifiable_stamp.to_json())
    except Exception as e:
        logger.error(f"message {msg_id} error broadcasting verifiable stamp: {e}")
        raise
    logger.info(f"message {msg_id} is now verifiable")
    await last_success.update(bot, seqno)
