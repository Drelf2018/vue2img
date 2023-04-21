import asyncio
import time
from typing import Union

from PIL import Image

from danmakus import ukamnads
from vue2img import createApp, word2cloud, getCuttedBody


async def main(uid: Union[int, str]):
    uk = ukamnads()
    liveid = await uk.get_last_liveid(uid)
    live = await uk.get_live(liveid)

    dms = uk.get_danmakus(live)
    channel = uk.get_channel(live)
    detail = uk.get_detail(live)

    gift, guard, superchat = uk.get_income(live)
    total_income = gift + guard + superchat

    line_width = 850
    income = Image.new('RGBA', (line_width, 50), (132, 212, 155) if guard != 0.0 else 'grey')
    if total_income:
        income.paste((255, 168, 180), (0, 0, int(line_width * gift / total_income), 50))
        income.paste((74, 194, 246), (int(line_width * (total_income - superchat) / total_income), 0, line_width, 50))

    bg = Image.new("L", (850, 300), "black")
    wc = word2cloud("/".join(dms), bg)

    nanami = getCuttedBody(Image.open("nana7mi.png"))

    t2s = lambda tt: time.strftime('%m/%d %H:%M', time.localtime(tt//1000))

    detail.update({
        "uName": channel["uName"],
        "time": t2s(detail["startDate"]) + " - " + t2s(detail["stopDate"]),
        
        "density": str(detail["danmakusCount"] * 60000 // (detail["stopDate"] - detail["startDate"])) + " / min",
        "gift": gift,
        "guard": guard,
        "superchat": superchat,
        
        "dm": wc,
        "income": income,
        "nanami": nanami,
    })
    createApp(1000).mount(path=".\Live.vue", data=detail).export("export.png")


asyncio.run(main(434334701))