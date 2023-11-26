import asyncio

import httpx


def create_get_req(
    client: httpx.AsyncClient,
    interval: int = 3,
    timeout: float = 5.0,
):
    async def async_get(
        url: str,
        headers: dict[str, str] = {},
    ):
        for _ in range(3):
            try:
                res = await client.get(
                    url, headers=headers, timeout=timeout, follow_redirects=True
                )
                if res.status_code == 200:
                    return res
                else:
                    # logger.error(
                    #     f"{url} : status code {str(res.status_code)} : {res.text}"
                    # )
                    print(f"{url} : status code {str(res.status_code)} : {res.text}")

            except Exception as e:
                # logger.error(f"{url} : {str(e)}")
                print(e)
                await asyncio.sleep(interval)

        return None

    return async_get
