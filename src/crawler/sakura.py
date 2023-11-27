import asyncio
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from pykakasi import kakasi

from .base import Base, Crawler

kks = kakasi()

base_url = "https://sakurazaka46.com"


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
            client,
            crawler,
            kanji_name,
            english_name,
            code,
            no,
            base_url,
            "sakura",
            date,
        )

    async def run(self):
        await super().run(self.page, 0)

    async def page(self, page_no: int):
        url = base_url + f"/s/s46/diary/blog/list?page={str(page_no)}&ct={self.code}"
        res = await self.async_get(url, self.logger)
        if res is None:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select(".com-blog-part li.box")

        if len(articles) == 0:
            return

        for article in articles:
            path = article.find("a")["href"]
            date_tag = article.find("p", {"class": "date"})
            date = datetime.strptime(date_tag.text, "%Y/%m/%d")
            if self.check_date(date):
                return

            await self.article(path, date)

        await self.page(page_no + 1)

    async def article(self, path: str, date: datetime):
        url = self.base_url + path
        res = await self.async_get(url, self.logger)
        if res is None:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        article = soup.find("div", {"class": "box-article"})
        await self.crawler.put_todo(self.collect_image(date, article), self.logger)


async def get_member_info(client: httpx.AsyncClient):
    url = base_url + "/s/s46/search/artist?display=syllabary"
    res = await client.get(url)
    bs4_blog = BeautifulSoup(res.text, "html.parser")
    members = bs4_blog.select(".member-elem li.box")

    list_ = []
    for member in members:
        code = member["data-member"]
        kanji = member.find("p", {"class": "name"}).get_text().strip()
        kana = member.find("p", {"class": "kana"}).get_text().strip()
        last = kana.split()[0]
        first = kana.split()[1]
        first = kks.convert(first)[0]["hepburn"]
        last = kks.convert(last)[0]["hepburn"]
        english = first + "_" + last

        list_.append(
            {
                "kanji_name": kanji,
                "english_name": english,
                "code": code,
                "no": 0,
                "date": None,
            }
        )

    return list_
