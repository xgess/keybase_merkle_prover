import asyncio
import logging
import json
from binascii import hexlify
import os
import re
from base64 import b64decode, b64encode
import subprocess
import shutil

from pykeybasebot import Bot
import pykeybasebot.types.chat1 as chat1
import requests
from opentimestamps.core.timestamp import DetachedTimestampFile


EXPECTED_MAGIC_BYTES = DetachedTimestampFile.HEADER_MAGIC


async def broadcast_new_root(bot):
    logging.debug("broadcasting a new root")
    keybase_kid = '010159baae6c7d43c66adf8fb7bb2b8b4cbe408c062cfc369e693ccb18f85631dbcd0a'
    url = "https://keybase.io/_/api/1.0/merkle/root.json"

    response = requests.get(url)
    res = response.json()
    root_hash, seqno, ctime_string = res['hash'], res['seqno'], res['ctime_string']
    sig = re.compile(r"\n\n((\S|\n)*?)\n=").search(res['sigs'][keybase_kid]['sig']).group(1)
    sig = sig.replace('\n', '')  # throwaway newlines
    sig_data = b64decode(sig)

    result = subprocess.run(['ots', '-v', 'stamp'], input=sig_data, capture_output=True)
    if result.returncode is not 0:
        logging.error(f"STAMP returned something non-zero {result}")
        return

    if result.stdout[:len(EXPECTED_MAGIC_BYTES)] != EXPECTED_MAGIC_BYTES:
        logging.error("STAMP magic bytes don't match:", result.stdout)
        return

    kbmsg = {
        "version": 0,
        "root_hash": root_hash,
        "seqno": seqno,
        "ctime_string": ctime_string,
        "on_chain": False,
        "sig_over_merkle_root": sig,
        "ots_proof": b64encode(result.stdout).decode('UTF-8'),
    }
    await bot.chat.broadcast(json.dumps(kbmsg))



async def update_messages(bot):
    logging.debug("updating messages")
    channel = chat1.ChatChannel(name=bot.username, public=True)
    all_posts = await bot.chat.read(channel)
    for m in all_posts:
        try:
            kbmsg = json.loads(m.content.text.body)
            msg_id = m.id
        except:
            logging.debug(f"couldn't parse message {m.id}. continuing...")
            continue
        if kbmsg.get('version') != 0:
            continue
        if msg_id == 5:
            continue
        if kbmsg['on_chain'] is False:
            await update_ots_for_msg(bot, msg_id, kbmsg)


async def update_ots_for_msg(bot, msg_id, kbmsg):
    logging.debug(f"msg {msg_id} is not yet on chain")
    sig_data = b64decode(kbmsg['sig_over_merkle_root'])
    ots_data = b64decode(kbmsg['ots_proof'])

    # set up some temp files because ots doesn't handle
    # streams well for the `upgrade` command
    tmpdir = f"./tmp"
    data_path = os.path.join(tmpdir, str(msg_id))
    ots_path = f"{data_path}.ots"
    bak_path = f"{ots_path}.bak"
    cleanup(data_path, ots_path, bak_path)

    with open(data_path, 'wb') as f:
        f.write(sig_data)
    with open(ots_path, 'wb') as f:
        f.write(ots_data)

    result = subprocess.run(['ots', 'upgrade', ots_path], capture_output=True)
    logging.debug(f"UPGRADE {result}")
    if not_on_chain_yet(result):
        logging.debug(f'UPGRADE proof for {msg_id} is not on chain yet')
        cleanup(data_path, ots_path, bak_path)
        return
    if result.returncode != 0:
        logging.error(f'unexpected returncode {result.returncode} when upgrading {msg_id}')
        cleanup(data_path, ots_path, bak_path)
        return

    with open(ots_path, 'rb') as f:
        upgraded_data = f.read()

    if upgraded_data == ots_data:
        # nothing actually changed. bail.
        cleanup(data_path, ots_path, bak_path)
        return

    result = subprocess.run(
        ['ots', '--no-cache', '--no-bitcoin', '-v', 'verify', ots_path]
        , capture_output=True)
    logging.debug(f"VERIFY {result}")
    if not successfully_verified(result):
        logging.debug(f'something went wrong verifying proof for {msg_id}')
        result = subprocess.run(['ots', 'info', ots_path], capture_output=True)
        logging.debug(f"INFO {result}")
        logging.debug(f"ots data after upgrade: {upgraded_data}")
        cleanup(data_path, ots_path, bak_path)
        return

    cleanup(data_path, ots_path, bak_path)

    kbmsg['ots_proof'] = b64encode(upgraded_data).decode('UTF-8')
    kbmsg['on_chain'] = True
    kbmsg['btc_check'] = extract_verify_checks(result)
    channel = chat1.ChatChannel(name=bot.username, public=True)
    await bot.chat.edit(channel, msg_id, json.dumps(kbmsg))


def cleanup(*args):
    try:
        [ os.remove(f) for f in args ]
    except FileNotFoundError:
        pass

def not_on_chain_yet(ots_upgrade_result):
    pending_message = b"Pending confirmation in Bitcoin blockchain"
    return pending_message in ots_upgrade_result.stdout

def successfully_verified(ots_verify_result):
    return (
        b'Success! Timestamp complete' in ots_verify_result.stderr or
        b'To verify manually, check that Bitcoin block' in ots_verify_result.stderr
    )

def extract_verify_checks(ots_verify_result):
    # e.g. ['To verify manually, check that Bitcoin block 607429 has merkleroot 8ee50d75b...']
    lines = ots_verify_result.stderr.decode('utf-8').split('\n')
    relevant = [l for l in lines if l.startswith('To verify manually')]
    return relevant

