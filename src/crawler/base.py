import asyncio
import os
import re
from datetime import datetime
from typing import Iterable, List, Optional, TypedDict

import httpx
from bs4 import BeautifulSoup, Tag

from src.logger import Logger, create_logger
from src.recorder import Recorder, date_format
from src.requests import create_get_req

recorder = Recorder()

pattern = "http.*"
repatter = re.compile(pattern)

base_dir = os.path.join(os.getcwd(), "data")


class ImageInfo(TypedDict):
    url: str
    path: str


class Crawler:
    def __init__(
        self,
        client: httpx.AsyncClient,
        num_workers: int = 20,
        retry_count: int = 3,
    ):
        self.async_get = create_get_req(client)
        self.retry_count = retry_count

        self.todo: asyncio.Queue = asyncio.Queue(maxsize=num_workers * 3)
        self.workers = [
            asyncio.create_task(self._worker(i)) for i in range(num_workers)
        ]

    async def _worker(self, worker_index: int):
        while True:
            try:
                await self._process_one(worker_index)
            except asyncio.CancelledError:
                return

    async def _process_one(self, worker_index: int):
        info, logger = await self.todo.get()
        await self._download(info, logger, worker_index)
        self.todo.task_done()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.todo.join()
        for worker in self.workers:
            worker.cancel()

    async def put_todo(self, infos: Iterable[ImageInfo], logger: Logger):
        for info in infos:
            await self.todo.put((info, logger))

    async def _download(self, info: ImageInfo, logger: Logger, worker_index: int):
        res = await self.async_get(info["url"], logger=logger, worker=worker_index)
        if res is None:
            return

        with open(info["path"], "wb") as f:
            f.write(res.content)


class Base:
    def __init__(
        self,
        client: httpx.AsyncClient,
        crawler: Crawler,
        kanji_name: str,
        english_name: str,
        code: str,
        base_url: str,
        group: str,
        date: Optional[datetime] = None,
    ):
        self.logger = create_logger(english_name)
        self.async_get = create_get_req(client)
        self.crawler = crawler

        self.kanji_name = kanji_name
        self.english_name = english_name
        self.group = group
        self.code = code
        self.count: int = 0
        self.date: datetime = datetime.now()
        self.latest_date: datetime = date if date else datetime(2000, 1, 1)
        self.No: int = 0
        self.base_url = base_url
        self.dir = os.path.join(base_dir, group, kanji_name)
        make_dir(self.dir)

    def __str__(self):
        return f"{self.english_name}, new : {self.count}, total : {self.count_files()}"

    def __del__(self) -> None:
        try:
            os.rmdir(self.dir)
        except OSError as e:
            e
            pass

    async def run(self, func, *args):
        self.logger.info({"message": "start"})
        await func(*args)
        recorder.record[self.group][self.code] = {
            "name": self.kanji_name,
            "total": self.count_files(),
            "date": datetime.now()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .strftime(date_format),
        }
        self.logger.info({"message": "end", "count": self.count})

    def collect_image(self, date: datetime, soup: BeautifulSoup) -> List[ImageInfo]:
        self.logger.info(
            {"message": "collect image", "date": date.strftime("%Y-%m-%d")}
        )
        label = self.english_name + "-" + date.strftime("%Y%m%d")
        path = os.path.join(self.dir, label)

        imgs = soup.select("img")

        list_: List[ImageInfo] = []
        for img in imgs:
            self._check_no(date)
            res = self._get_img(img, path)
            if res is None:
                continue

            self.count += 1
            list_.append(res)

        return list_

    def _get_img(self, img: Tag, path: str) -> ImageInfo | None:
        href = img.get("src")
        if href is None:
            return None
        elif self._check_full_path(href):
            url = href
        else:
            url = self.base_url + href

        if ".jpg" in url or ".jpeg" in url or ".JPG" in url or ".JPEG" in url:
            path += str(self.No).zfill(4) + ".jpeg"
        elif ".png" in url or ".PNG" in url:
            path += str(self.No).zfill(4) + ".png"
        else:
            self.logger.error(f"not image ext : {url}")
            return None

        return {"url": url, "path": path}

    def _check_full_path(self, s: str) -> bool:
        result = repatter.search(s)
        return bool(result)

    def _check_no(self, date: datetime) -> None:
        if self.date.date() != date.date():
            self.No = 0
            self.date = date

        self.No += 1

    def count_files(self) -> int:
        return len(os.listdir(self.dir))

    def check_date(self, date: datetime):
        return self.latest_date >= date


def make_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path)
