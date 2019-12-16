from base64 import b64decode, b64encode
import logging
import os
import subprocess
from typing import Tuple

from opentimestamps.core.timestamp import DetachedTimestampFile


EXPECTED_MAGIC_BYTES = DetachedTimestampFile.HEADER_MAGIC
logger = logging.getLogger(__name__)


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


async def upgrade(identifier, raw_data, ots_data) -> Tuple[str, bool]:
    # is the result of upgrading the OTS and whether or not it's finalized
    # uses temp files because ots doesn't handle streams well for
    # the `upgrade` and `verify` and `info` commands
    tmpdir = f"../tmp"
    data_path = os.path.join(tmpdir, str(identifier))
    ots_path = f"{data_path}.ots"
    bak_path = f"{ots_path}.bak"

    try:
        with open(data_path, 'wb') as f:
            f.write(raw_data)
        with open(ots_path, 'wb') as f:
            f.write(ots_data)

        ots_data, is_final = await _upgrade(logger, identifier, data_path, ots_path)
        return ots_data, is_final

    finally:
        safe_delete(data_path)
        safe_delete(bak_path)
        safe_delete(ots_path)


async def _upgrade(logger, identifier, data_path, ots_path) -> Tuple[str, bool]:
    with open(ots_path, 'rb') as f:
        original_ots_data = f.read()

    result = subprocess.run(['ots', 'upgrade', ots_path], capture_output=True)
    if not_on_chain_yet(result):
        return original_ots_data, False
    if result.returncode != 0:
        raise UpgradeError(f'unexpected result {result}')

    logger.debug(f"ots upgrade result for {identifier}: {result}")
    with open(ots_path, 'rb') as f:
        upgraded_data = f.read()

    if upgraded_data == original_ots_data:
        # Nothing actually changed. That's weird and I don't think it should happen.
        raise UpgradeError(f"{identifier} ots data didn't change after an upgrade")

    result = subprocess.run(
        ['ots', '--no-cache', '--no-bitcoin', '-v', 'verify', ots_path],
        capture_output=True)
    if not successfully_verified(result):
        logger.debug(f'{identifier} did not verify')
        # uncomment these lines if something is broken. otherwise, it's spammy.
        # result = subprocess.run(['ots', 'info', ots_path], capture_output=True)
        # logger.debug(f"INFO {result}")
        # logger.debug(f"ots data after upgrade: {upgraded_data}")
        raise VerifyError(f"{identifier}: {result}")

    ots = b64encode(upgraded_data).decode('UTF-8')
    return ots, True


def safe_delete(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

def not_on_chain_yet(ots_upgrade_result):
    return (
        b"Pending confirmation in Bitcoin blockchain" in ots_upgrade_result.stderr or
        b"waiting for 5 confirmations" in ots_upgrade_result.stderr
    )


def successfully_verified(ots_verify_result):
    return (
        b'Success! Timestamp complete' in ots_verify_result.stderr or
        b'To verify manually, check that Bitcoin block' in ots_verify_result.stderr
    )
