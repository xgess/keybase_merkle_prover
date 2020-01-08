import asyncio


async def retry_if_timeout(logger, func, *args, **kwargs):
    for i in range(0, 100):
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
