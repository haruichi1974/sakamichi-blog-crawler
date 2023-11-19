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
        infos: Iterable[ImageInfo],
        workers: int = 10,
        retry_count: int = 3,
    ):
        self.client = client
        self.infos = infos
        self.num_workers = workers
        self.retry_count = retry_count

        self.todo: asyncio.Queue = asyncio.Queue()

    async def put_todo(self, infos: Iterable[ImageInfo]):
        for info in infos:
            await self.todo.put(info)

    async def run(self) -> None:
        await self.put_todo(self.infos)
        workers = [asyncio.create_task(self.worker()) for _ in range(self.num_workers)]
        await self.todo.join()

        for worker in workers:
            worker.cancel()

    async def worker(self):
        while True:
            try:
                await self.process_one()
            except asyncio.CancelledError:
                return

    async def process_one(self):
        info = await self.todo.get()
        for _ in range(self.retry_count):
            try:
                await self.download(info)
                break
            except Exception as e:
                print(e)
        self.todo.task_done()

    async def download(self, info: ImageInfo):
        await asyncio.sleep(0.1)

        res = await self.client.get(info["url"], follow_redirects=True)

        with open(info["path"], "wb") as f:
            f.write(res.content)
