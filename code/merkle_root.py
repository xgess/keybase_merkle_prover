from base64 import b64decode, b64encode
from contextlib import redirect_stderr
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import hashlib
import io
import json
import logging
import re

from pgpy import PGPKey, PGPMessage
import requests


KEYBASE_MERKLE_ROOT_URL = 'https://keybase.io/_/api/1.0/merkle/root.json'
TEMPLATE_MERKLE_URL = KEYBASE_MERKLE_ROOT_URL + "?seqno={seqno}"
KEYBASE_KID = '010159baae6c7d43c66adf8fb7bb2b8b4cbe408c062cfc369e693ccb18f85631dbcd0a'
logger = logging.getLogger(__name__)


class VerificationError(Exception):
    pass


@dataclass_json
@dataclass
class MerkleRoot:
    # if the format of anything in here changes, make sure to
    # bump the version of StampedMerkleRoot
    seqno: int = 0
    ctime_string: str = "1970-01-01T00:00:00.000Z"
    root_hash: str = 128 * "0"
    b64stamped: str = 128 * "0"  # hash of validated sig over merkle root payload
    stable_url: str = TEMPLATE_MERKLE_URL.format(seqno=0)

    @property
    def data_to_stamp(self) -> bytes:
        return b64decode(self.b64stamped)


# fetch from the keybase API and verify a bunch of things
def fetch_keybase_merkle_root() -> MerkleRoot:
    # fetch the current merkle root from the keybase api
    resp = requests.get(KEYBASE_MERKLE_ROOT_URL)
    full_kb_merkle_root = resp.json()
    seqno = full_kb_merkle_root['seqno']
    stable_url = TEMPLATE_MERKLE_URL.format(seqno=seqno)
    root_hash = full_kb_merkle_root['hash']

    # extract the signature and signed payload into a PGP message for verification
    raw_pgp_sig_msg = full_kb_merkle_root['sigs'][KEYBASE_KID]['sig']

    # the message itself is too big to include with OTS data in a chat message
    # so let's take the hash of it and use that instead. this is kind of a
    # bummer because it's almost OK to use the whole thing.
    hash_of_raw_pgp_sig = hashlib.sha512(raw_pgp_sig_msg.encode()).digest()
    b64stamped = b64encode(hash_of_raw_pgp_sig).decode('utf-8')

    # this function will raise an exception if PGP verification fails
    signed_payload = _verify_keybase_signature(raw_pgp_sig_msg)

    # as a sanity check, ensure that the signed payload matches
    # the raw json payload which is also present in the keybase
    # API response
    claimed_payload = json.loads(full_kb_merkle_root['payload_json'])
    if signed_payload != claimed_payload:
        logger.error(f"signed_payload: {signed_payload}")
        logger.error(f"api response payload: {claimed_payload}")
        raise VerificationError(f"signed payload doesn't match API response payload at {stable_url}")

    # and most importantly, that the root hash that was signed is the same as the one that's
    # at the top level of the API response body.
    signed_root_hash = signed_payload['body']['root']
    if (signed_root_hash != root_hash or len(signed_root_hash) == 0):
        logger.error(f"signed_payload: {signed_payload}")
        raise VerificationError(f"keybase signed a different root hash ({signed_root_hash}) from the one in the payload {root_hash}")

    return MerkleRoot(
        seqno=seqno,
        root_hash=root_hash,
        ctime_string=full_kb_merkle_root['ctime_string'],
        b64stamped=b64stamped,
        stable_url=stable_url,
    )


def _verify_keybase_signature(raw_pgp_sig_msg):
    # load the raw pgp message
    pgp_msg = PGPMessage.from_blob(raw_pgp_sig_msg)
    # load keybase's claimed public key
    # see: https://keybase.io/docs/server_security/our_merkle_key
    kb_public_key, _ = PGPKey.from_blob(KEYBASE_PGP_VERIFICATION_KEY)

    # verify it: https://pgpy.readthedocs.io/en/latest/examples.html#verifying-things
    f = io.StringIO()
    with redirect_stderr(f):
        # suppress unnecessary stdout
        verification_result = kb_public_key.verify(pgp_msg)
    if not verification_result:
        raise VerificationError("API response did not verify with Keybase's public key")

    good_signatures = list(verification_result.good_signatures)
    if len(good_signatures) != 1:
        logger.error(f"good_signatures = {good_signatures}")
        raise VerificationError(f"Expected 1 valid signature, got {len(good_signatures)} from {specific_url}")

    return json.loads(good_signatures[0].subject)



KEYBASE_PGP_VERIFICATION_KEY = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG/MacGPG2 v2.0.22 (Darwin)
Comment: GPGTools - https://gpgtools.org

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
SLOcqa+kq/vL6AXsXFpFr+ovOrU=
=veW2
-----END PGP PUBLIC KEY BLOCK-----
"""