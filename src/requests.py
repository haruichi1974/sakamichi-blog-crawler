import asyncio

import httpx

from .logger import Logger


def create_get_req(
    client: httpx.AsyncClient,
    interval: int = 3,
    timeout: float = 5.0,
):
    async def async_get(
        url: str,
        logger: Logger,
        headers: dict[str, str] = {},
        worker: int | None = None,
    ):
        logger.debug({"request": url, "worker": worker})
        await asyncio.sleep(0.5)
        for _ in range(3):
            try:
                res = await client.get(
                    url, headers=headers, timeout=timeout, follow_redirects=True
                )
                if res.status_code == 200:
                    return res

                logger.error(
                    {
                        "url": url,
                        "status code": res.status_code,
                        "message": res.text,
                        "worker": worker,
                    }
                )
                if res.status_code == 404:
                    return None

            except Exception as e:
                logger.error({"url": url, "Exception": e, "worker": worker})
                await asyncio.sleep(interval)

        return None

    return async_get
