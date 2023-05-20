import sys
import time
from io import BytesIO
from typing import Union

import httpx
from bilibili_api import user
from danmakus import ukamnads
from PIL import Image, ImageDraw

sys.path.append("..") 
from vue2img import Template, createApp


class LiveTemplate(Template):
    async def get_face(self, uid: int = 434334701, debug: bool = False) -> Image.Image:
        if debug:
            return Image.new('RGBA', (150, 150), "skyblue")

        # 爬取装扮及头像
        js = await user.User(uid).get_user_info()
        # 头像
        if face := js.get('face'):
            response = httpx.get(face)  # 请求图片
            face = Image.open(BytesIO(response.read()))  # 读取图片
            w, h = face.size
            a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
            ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形

        # 装扮
        if pendant := js.get('pendant', {}).get('image'):
            response = httpx.get(pendant)  # 请求图片
            pendant = Image.open(BytesIO(response.read()))  # 读取图片
            pendant = pendant.convert('RGBA')

            bg = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
            bg.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
            pendant = pendant.resize((int(1.75*w), int(1.75*h)), Image.LANCZOS)  # 装扮应当是头像的1.75倍
            try:
                bg.paste(pendant, (0, 0), mask=pendant.getchannel('A'))  # 粘贴至背景
            except Exception:
                pendant = None
        # 粉圈
        if not pendant:
            image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
            image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
            ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
            a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
            ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
            ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
            image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
            w, h = image.size
            bg = Image.new('RGBA', (int(1.25*w), int(1.25*h)), (0, 0, 0, 0))
            bg.paste(image, (int((1.25-1)/2*w), int((1.25-1)/2*h)))

        return bg

    async def data(self, uid: Union[int, str]):
        uk = ukamnads()
        liveid = await uk.get_last_liveid(uid)
        live = await uk.get_live(liveid)

        channel = uk.get_channel(live)
        detail = uk.get_detail(live)

        gift, guard, superchat, total_income = uk.get_income(live)

        line_width = 850
        income = Image.new('RGBA', (line_width, 50), (132, 212, 155) if guard != 0.0 else 'grey')
        if total_income:
            income.paste((255, 168, 180), (0, 0, int(line_width * gift / total_income), 50))
            income.paste((74, 194, 246), (int(line_width * (total_income - superchat) / total_income), 0, line_width, 50))

        bg = Image.new("RGB", (850, 300), "skyblue")

        # 如果这里获取不到头像 可以 debug=True
        face = await self.get_face(uid, debug=False)

        t2s = lambda tt: time.strftime('%m/%d %H:%M', time.localtime(tt // 1000))

        if detail["stopDate"] == 0:
            time_str = " (在播)"
            detail["stopDate"] = 1000 * int(time.time())
        else:
            time_str = ""

        time_str = t2s(detail["startDate"]) + " - " + t2s(detail["stopDate"]) + time_str
        
        detail.update({
            "uName": channel["uName"],
            "time": time_str,
            
            "density": str(detail["danmakusCount"] * 60000 // (detail["stopDate"] - detail["startDate"])) + " / min",
            "gift": gift,
            "guard": guard,
            "superchat": superchat,
            "income": total_income,
            
            "dm": bg,
            "incomeLine": income,
            "face": face,
            "nanami": False
        })

        return detail


App = LiveTemplate(path="Live.vue", uid=434334701)
app = createApp(App).mount().show()
