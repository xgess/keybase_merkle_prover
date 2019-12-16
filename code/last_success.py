import logging


NAMESPACE = "keybase_merkle_prover"
ENTRY_KEY = "last_successful_verification"
logger = logging.getLogger(__name__)


async def update(bot, seqno) -> None:
    team_name = f"{bot.username},{bot.username}"
    try:
        res = await bot.kvstore.get(team_name, NAMESPACE, ENTRY_KEY)
        prev_seqno = int(res.entry_value or 0)
        if seqno > prev_seqno:
            # don't overwrite if I wind up doing these things out of order
            await bot.kvstore.put(team_name, NAMESPACE, ENTRY_KEY, str(seqno))
        else:
            logger.debug(f"verified a seqno out of order. not updating from {str(prev_seqno)} to {seqno}")
    except Exception as e:
        # this functionality is entirely a nice-to-have, so I don't
        # really care if it errors
        logger.error(f"kvstore update error: {e}")
    return


async def fetch(bot) -> int:
    team_name = f"{bot.username},{bot.username}"
    try:
        res = await bot.kvstore.get(team_name, NAMESPACE, ENTRY_KEY)
        seqno = int(res.entry_value or 0)
    except Exception as e:
        # this functionality is entirely a nice-to-have, so I don't
        # really care if it errors
        logger.error(f"kvstore fetch error: {e}")
        seqno = 0
    return seqno
