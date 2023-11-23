from __future__ import annotations

import asyncio
from typing import Iterable, TypedDict

import httpx  # https://github.com/encode/httpx


class ImageInfo(TypedDict):
    url: str
    path: str


class Downloader:
    def __init__(
        self,
        client: httpx.AsyncClient,
        num_workers: int = 10,
        retry_count: int = 3,
    ):
        self.client = client
        self.retry_count = retry_count

        self.todo: asyncio.Queue = asyncio.Queue()
        self.workers = [
            asyncio.create_task(self._worker(i)) for i in range(num_workers)
        ]

    async def _worker(self, worker_index: int):
        while True:
            try:
                await self._process_one()
            except asyncio.CancelledError:
                return

    async def _process_one(self):
        info = await self.todo.get()
        print(info)
        for _ in range(self.retry_count):
            try:
                await self._download(info)
                break
            except Exception as e:
                print(e)
        self.todo.task_done()

    async def _download(self, info: ImageInfo):
        await asyncio.sleep(0.1)

        res = await self.client.get(info["url"], follow_redirects=True)

        with open(info["path"], "wb") as f:
            f.write(res.content)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.todo.join()
        for worker in self.workers:
            worker.cancel()

    async def put_todo(self, infos: Iterable[ImageInfo]):
        for info in infos:
            await self.todo.put(info)


async def example():
    async with httpx.AsyncClient() as client:
        async with Downloader(client, 5, 1) as downloader:
            await downloader.put_todo()
            pass


if __name__ == "__main__":
    asyncio.run(example(), debug=True)
