import asyncio
import time

import httpx

from src.crawler import base, hinata, nogi, sakura


async def async_run():
    async with httpx.AsyncClient() as client:
        n_infos = await nogi.get_member_info(client)
        s_infos = await sakura.get_member_info(client)
        h_infos = await hinata.get_member_info(client)
        async with base.Crawler(client) as crawler:
            collectors = []

            for info in n_infos:
                collectors.append(
                    nogi.Collector(client=client, crawler=crawler, **info)
                )

            for info in s_infos:
                collectors.append(
                    sakura.Collector(client=client, crawler=crawler, **info)
                )

            for info in h_infos:
                collectors.append(
                    hinata.Collector(client=client, crawler=crawler, **info)
                )

            cors = [c.run() for c in collectors]
            await asyncio.gather(*cors)


def main() -> None:
    start = time.perf_counter()
    asyncio.run(async_run(), debug=True)
    end = time.perf_counter()

    print(f"Done in {end - start:.2f}s")


if __name__ == "__main__":
    main()
