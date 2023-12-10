from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from pykakasi import kakasi

from src.recorder import Recorder, date_format

from .base import Base, Crawler

recorder = Recorder()
record_getter = recorder.call_getter("hinata")

kks = kakasi()

base_url = "https://www.hinatazaka46.com/s/official/"


class Collector(Base):
    def __init__(
        self,
        client: httpx.AsyncClient,
        crawler: Crawler,
        kanji_name: str,
        english_name: str,
        code: str,
        date: datetime | None = None,
    ):
        super().__init__(
            client,
            crawler,
            kanji_name,
            english_name,
            code,
            base_url,
            "hinata",
            date,
        )

    async def run(self):
        await super().run(self.page, 0)

    async def page(self, page_no: int):
        url = base_url + f"diary/member/list?page={str(page_no)}&ct={self.code}"
        res = await self.async_get(url, self.logger)
        if res is None:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select(".p-blog-article")

        if len(articles) == 0:
            return

        for article in articles:
            date_tag = (
                article.find("div", {"class": "c-blog-article__date"})
                .get_text()
                .strip()
            )
            date = datetime.strptime(date_tag, "%Y.%m.%d %H:%M")
            if self.check_date(date):
                return

            await self.article(article, date)

        await self.page(page_no + 1)

    async def article(self, article: BeautifulSoup, date: datetime):
        await self.crawler.put_todo(self.collect_image(date, article), self.logger)


async def get_member_info(client: httpx.AsyncClient):
    url = base_url + "search/artist"

    res = await client.get(url)

    bs4_blog = BeautifulSoup(res.text, "html.parser")
    members = bs4_blog.select(".sort-default li")

    list_ = []
    for member in members:
        code = member.get("data-member")

        kanji = member.find("div", {"class": "c-member__name"}).get_text().strip()
        name_kana = member.find("div", {"class": "c-member__kana"}).get_text().strip()
        last = name_kana.split()[0]
        first = name_kana.split()[1]
        first = kks.convert(first)[0]["hepburn"]
        last = kks.convert(last)[0]["hepburn"]
        english = first + "_" + last

        record = record_getter(code)
        date = None
        if record is not None:
            date = datetime.strptime(record.get("date"), date_format)

        list_.append(
            {
                "kanji_name": kanji,
                "english_name": english,
                "code": code,
                "date": date,
            }
        )

    record = record_getter("000")
    date = None
    if record is not None:
        date = datetime.strptime(record.get("date"), date_format)

    list_.append(
        {
            "kanji_name": "ポカ",
            "english_name": "poka",
            "code": "000",
            "date": date,
        }
    )

    return list_
