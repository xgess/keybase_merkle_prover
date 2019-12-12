import asyncio
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from enum import Enum
import logging
import json
import re
from typing import List

import pykeybasebot.types.chat1 as chat1
import requests

import kb_ots


class ProofStatus(Enum):
    PRELIMINARY = "PRELIMINARY"
    SUPERSEDED = "SUPERSEDED"
    VERIFIABLE = "VERIFIABLE"


@dataclass_json
@dataclass
class KeybaseMerkleProof:
    seqno: int = 0
    ctime_string: str = "1970-01-01T00:00:00.000Z"
    kb_merkle_root: str = ""
    kb_sig: str = ""
    ots: str = ""
    version: int = 0
    status: ProofStatus = ProofStatus.PRELIMINARY
    bitcoin_checks: List[str] = field(default_factory=lambda: [])


async def broadcast_new_root(bot):
    logging.debug("broadcasting a new root")
    keybase_kid = '010159baae6c7d43c66adf8fb7bb2b8b4cbe408c062cfc369e693ccb18f85631dbcd0a'
    url = "https://keybase.io/_/api/1.0/merkle/root.json"

    response = requests.get(url)
    res = response.json()
    kb_merkle_root, seqno, ctime_string = res['hash'], res['seqno'], res['ctime_string']
    sig = re.compile(r"\n\n((\S|\n)*?)\n=").search(res['sigs'][keybase_kid]['sig']).group(1)
    sig = sig.replace('\n', '')
    sig_data = b64decode(sig)

    try:
        ots = await kb_ots.stamp(sig_data)
    except kb_ots.StampError as e:
        logging.error(e)
        return

    kb_proof = KeybaseMerkleProof(
        seqno=seqno,
        ctime_string=ctime_string,
        kb_merkle_root=kb_merkle_root,
        kb_sig=sig,
        ots=ots,
    )
    res = await bot.chat.broadcast(kb_proof.to_json())
    logging.info(f"broadcasted new root at msg_id {res.message_id}")


async def update_messages(bot):
    channel = chat1.ChatChannel(name=bot.username, public=True)
    all_posts = await bot.chat.read(channel) # paginate this and only pull recents
    for m in reversed(all_posts):
        try:
            kb_proof = KeybaseMerkleProof.from_json(m.content.text.body)
            msg_id = m.id
        except:
            logging.debug(f"couldn't parse message {m.id}. nothing to do here...")
            continue
        if kb_proof.version != 0:
            logging.debug(f"message {m.id} has an old version. nothing to do here...")
            continue
        logging.debug(f"message {m.id} has status {kb_proof.status}")
        if kb_proof.status is ProofStatus.PRELIMINARY:
            await update_ots_for_msg(bot, msg_id, kb_proof)
            await asyncio.sleep(1)  # necessary for broadcasting to succeed :/


async def update_ots_for_msg(bot, msg_id, kb_proof):
    logging.debug(f"msg {msg_id} is not yet on chain")
    sig_data = b64decode(kb_proof.kb_sig)
    ots_data = b64decode(kb_proof.ots)

    try:
        completed_ots, bitcoin_checks = await kb_ots.upgrade(
            identifier=msg_id,
            raw_data=sig_data,
            ots_data=ots_data,
        )
    except (kb_ots.VerifyError, kb_ots.UpgradeError) as e:
        logging.debug(e)
        return

    superseded_kb_proof = KeybaseMerkleProof.replace(kb_proof,
        status=ProofStatus.SUPERSEDED,
        ots="",
        kb_sig="",
    )
    verifiable_kb_proof = KeybaseMerkleProof.replace(kb_proof,
        status=ProofStatus.VERIFIABLE,
        ots=completed_ots,
        bitcoin_checks=bitcoin_checks,
    )
    channel = chat1.ChatChannel(name=bot.username, public=True)

    # broadcast the update and delete the previous message
    logging.info(f"{msg_id} is ready to be updated")
    await bot.chat.broadcast(verifiable_kb_proof.to_json())
    await bot.chat.edit(channel, msg_id, superseded_kb_proof.to_json())
