import asyncio
import json
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from pykakasi import kakasi

from .base import Base, Crawler

base_url = "https://www.nogizaka46.com"
headers = {"Accept": "application/json"}
limit = 20

const_list = [
    {"code": "40001", "kanji": "新4期生", "english": "new.fourth"},
    {"code": "40003", "kanji": "運営スタッフ", "english": "staff"},
    {"code": "40004", "kanji": "3期生", "english": "third"},
    {"code": "40005", "kanji": "4期生", "english": "fourth"},
    {"code": "40006", "kanji": "研修生", "english": "kensyusei"},
    {"code": "40007", "kanji": "5期生", "english": "fifth"},
]


class Collector(Base):
    def __init__(
        self,
        client: httpx.AsyncClient,
        crawler: Crawler,
        kanji_name: str,
        english_name: str,
        code: str,
        no: int,
        date: datetime | None = None,
    ):
        super().__init__(
            client, crawler, kanji_name, english_name, code, no, base_url, "nogi", date
        )

    async def run(self):
        await super().run(self.page, 0)

    async def page(self, offset: int):
        url = (
            base_url
            + f"/s/n46/api/list/blog?rw={str(limit)}&st={str(offset)}&ct={self.code}&callback=res"
        )
        res = await self.async_get(url, self.logger)
        if res is None:
            return

        article_data = parse_json(res.text)
        articles: list[dict] = article_data.get("data")
        if len(articles) == 0:
            return

        for article in articles:
            date_text = article["date"]
            date = datetime.strptime(date_text, "%Y/%m/%d %H:%M:%S")
            if self.check_date(date):
                return
            text = article["text"]
            soup = BeautifulSoup(text, "html.parser")

            if self.check_date(date):
                return

            await self.article(soup, date)

        await self.page(offset + limit)

    async def article(self, article: BeautifulSoup, date: datetime):
        await self.crawler.put_todo(self.collect_image(date, article), self.logger)


async def get_member_info(client: httpx.AsyncClient):
    url = base_url + "/s/n46/api/list/member?callback=res"
    res = await client.get(url)
    res_json = parse_json(res.text)

    member_data = res_json.get("data")
    if member_data is None:
        return []

    list_ = []
    for member in member_data:
        if member["english_name"] != "":
            english = member["english_name"].split(" ")
            english = english[1] + "_" + english[0]
            code = member["code"]
            list_.append(
                {
                    "kanji_name": member["name"],
                    "english_name": english,
                    "code": code,
                    "no": 0,
                    "date": None,
                }
            )

    for c in const_list:
        list_.append(
            {
                "kanji_name": c["kanji"],
                "english_name": c["english"],
                "code": c["code"],
                "no": 0,
                "date": None,
            }
        )

    return list_


def parse_json(text):
    json_text = text.strip("res(").rstrip(");")
    return json.loads(json_text)
