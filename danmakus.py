"""
基于 danmakus.com 的爬虫工具
"""

import asyncio
from typing import List

from weibo_poster import Request


class ukamnads(Request):
    "基于 api.ukamnads.icu 的弹幕爬虫"

    def __init__(self, base_url: str = "https://api.ukamnads.icu/api/v2"):
        super().__init__()
        self.session.base_url = base_url

    async def get_last_liveid(self, uid: int | str) -> str | None:
        "获取最近直播序号"

        data: dict = await self.request("GET", "/channel", params={"uId": uid})
        lives: List[dict] = data.get("data", {}).get("lives", [])
        if len(lives) != 0:
            return lives[0].get("liveId", None)
        
    async def get_live(self, liveid: str) -> dict:
        "获取直播数据"

        assert liveid is not None, "liveid can't be None"
        return await self.request("GET", "/live", params={"liveId": liveid})

    def get_channel(self, live: dict) -> dict:
        "直播生涯数据"

        return live.get("data", {}).get("data", {}).get("channel", {})

    def get_detail(self, live: dict) -> dict:
        "该场直播数据"

        return live.get("data", {}).get("data", {}).get("live", {})

    def get_danmakus(self, live: dict) -> List[str]:
        "该场直播弹幕文本"

        messages = list()
        danmakus: List[dict] = live.get("data", {}).get("data", {}).get("danmakus", [])
        for dm in danmakus:
            mes: str = dm.get("message", "")
            if mes.strip() != "":
                messages.append(mes)
        return messages

    async def get_last_live_messages_all_in_one_string_by_uid(self, uid: int | str, junction: str = "/"):
        "异步获取拼接后直播弹幕文本"

        liveid = await self.get_last_liveid(uid)
        live = await self.get_live(liveid)
        dms = self.get_danmakus(live)
        return junction.join(dms)
    
    @staticmethod
    def sync_get_last_live_messages_all_in_one_string_by_uid(uid: int | str, junction: str = "/"):
        "同步获取拼接后直播弹幕文本"

        return asyncio.new_event_loop().run_until_complete(ukamnads().get_last_live_messages_all_in_one_string_by_uid(uid, junction))
    
    @staticmethod
    def sd(uid: int | str, junction: str = "/"):
        "同本"

        return ukamnads.sync_get_last_live_messages_all_in_one_string_by_uid(uid, junction)
