from base64 import b64decode, b64encode
import logging
import os
import subprocess

from opentimestamps.core.timestamp import DetachedTimestampFile


EXPECTED_MAGIC_BYTES = DetachedTimestampFile.HEADER_MAGIC


class StampError(Exception):
    pass

class UpgradeError(Exception):
    pass

class VerifyError(Exception):
    pass


async def stamp(raw_data):
    result = subprocess.run(['ots', '-v', 'stamp'], input=raw_data, capture_output=True)
    if result.returncode is not 0:
        raise StampError(f"STAMP returned something non-zero {result}")

    if result.stdout[:len(EXPECTED_MAGIC_BYTES)] != EXPECTED_MAGIC_BYTES:
        raise StampError(f"STAMP magic bytes don't match: {result.stdout}")

    return b64encode(result.stdout).decode('UTF-8')


async def upgrade(identifier, raw_data, ots_data):
    # set up temp files because ots doesn't handle
    # streams well for the `upgrade` command
    tmpdir = f"../tmp"
    data_path = os.path.join(tmpdir, str(identifier))
    ots_path = f"{data_path}.ots"
    bak_path = f"{ots_path}.bak"

    try:
        with open(data_path, 'wb') as f:
            f.write(raw_data)
        with open(ots_path, 'wb') as f:
            f.write(ots_data)

        return await _upgrade(identifier, data_path, ots_path)

    finally:
        safe_delete(data_path)
        safe_delete(bak_path)
        safe_delete(ots_path)


async def _upgrade(identifier, data_path, ots_path):
    with open(ots_path, 'rb') as f:
        original_ots_data = f.read()

    result = subprocess.run(['ots', 'upgrade', ots_path], capture_output=True)
    logging.debug(f"UPGRADE {result}")
    if not_on_chain_yet(result):
        raise UpgradeError(f'UPGRADE proof for {identifier} is not on chain yet')
    if result.returncode != 0:
        raise UpgradeError(f'unexpected returncode {result.returncode} when upgrading {identifier}')

    with open(ots_path, 'rb') as f:
        upgraded_data = f.read()

    if upgraded_data == original_ots_data:
        logging.debug(f"{identifier} ots data didn't change. bail. ")
        # nothing actually changed. bail.
        return

    result = subprocess.run(
        ['ots', '--no-cache', '--no-bitcoin', '-v', 'verify', ots_path]
        , capture_output=True)
    logging.debug(f"VERIFY {result}")
    if not successfully_verified(result):
        logging.debug(f'{identifier} did not verify')
        # uncomment these lines if something is broken. otherwise, it's spammy.
        # result = subprocess.run(['ots', 'info', ots_path], capture_output=True)
        # logging.debug(f"INFO {result}")
        # logging.debug(f"ots data after upgrade: {upgraded_data}")
        raise VerifyError()

    ots = b64encode(upgraded_data).decode('UTF-8')
    return ots


def safe_delete(path):
    try:
        os.remove(path)
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
