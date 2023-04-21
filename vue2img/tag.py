from io import BytesIO, TextIOWrapper
from typing import Tuple

import httpx
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from .template import template
from .operation import radiusMask
from .font import FontWeight


class Tag:
    def __init__(self, tag: str, data: dict, parent: "Tag" = None):
        # 节点信息
        self.tag = tag
        self.parent = parent
        self.depth = parent.depth + 1

        # 基础 style
        self.style = data.pop("style", {})
        self.position = self.style.get("position", "static")

        # 计算 先计算字号再计算宽度
        self.font_size, = self.calc("font-size")
        self.width, = self.calc("width")

        # 计算 margin padding
        self.m0, self.m1, self.m2, self.m3 = self.outside("margin")
        self.p0, self.p1, self.p2, self.p3 = self.outside("padding")

        # 子节点信息
        children = data.pop("children", [])
        self.children = list(map(self.makeTag, children))
        self.__dict__.update(data)

        # 导出 html
        tt = "\n" + "  " * (self.depth-1)
        self.repr = tt.join(map(str, self.children))

    def makeTag(self, data: dict | str):
        "创建子节点"

        if isinstance(data, str):
            return TextTag(data, self)
        tag = data.pop("tag", "body")
        match tag:
            case "img":
                return ImgTag(data, self)
            case _:
                return Tag(tag, data, self)

    def __repr__(self):
        tt = "  " * self.depth
        return f'{tt}<{self.tag} id="{self.id}">\n{self.repr}\n{tt}</{self.tag}>'

    @property
    def id(self):
        return f"{self.tag}{id(self)}"

    @property
    def css(self):
        cs = ["#" + self.id + " {\n" + "\n".join([f"  {k}: {v};" for k, v in self.style.items()]) + "\n}"]
        for c in self.children:
            cs += c.css
        return cs

    @property
    def element(self) -> etree._Element:
        return etree.HTML(str(self))

    def toFloat(self, key: str = "", value: str = "") -> float:
        "转换单位 例如 px em %"

        if value.endswith("px"):
            return float(value[:-2])
        if value.endswith("%"):
            if key == "width":
                return float(value[:-1]) * self.parent.width / 100
            elif key == "font-size":
                return float(value[:-1]) * self.parent.font_size / 100
            else:
                return float(value[:-1]) * self.width / 100
        elif value.endswith("em"):
            if key == "font-size":
                return float(value[:-2]) * self.parent.font_size
            else:
                return float(value[:-2]) * self.font_size
        elif value == "auto":
            return self.parent.font_size if key == "font-size" else self.parent.width
        return float(value)

    def calc(self, key: str, value: str = "auto") -> Tuple[float, ...]:
        "计算 style 表达式"

        alpha = self.style.get(key, value)
        alpha = str(alpha)  # 强制转换

        args = alpha.replace("(", " ( ").replace(")", " ) ").split(" ")
        arg = ""
        expr = list()
        inner = 0

        for val in args:
            # 判空
            if val == "calc" or val == "":
                continue

            # 计算括号层数
            if val.startswith("("):
                inner += 1
            elif val.endswith(")"):
                inner -= 1

            # 组合算子
            if val in ["+", "-", "*", "/", "(", ")"]:
                arg += val
            else:
                arg += str(self.toFloat(key, val))

            # 在括号最外层则添加
            if inner == 0:
                expr.append(arg)
                arg = ""

        return tuple(map(eval, expr))

    def setSize(self) -> float:
        self.height = 0

        inline = 0
        lm = 0
        for c in self.children:
            h = c.setSize()
            if c.position == "absolute":
                continue
            if c.style.get("display", "block").startswith("inline"):
                inline = max(inline, max(lm, c.m0) + c.p0 + h + c.p2)
                continue
            else:
                self.height += inline + max(lm, c.m0) + c.p0 + h + c.p2
                inline = 0
            self.height += max(lm, c.m0) + c.p0 + h + c.p2
            lm = c.m2
        else:
            self.height += lm

        # 强制覆盖高度
        self.height, = self.calc("height", self.height)

        return self.height

    def outside(self, key: str) -> Tuple[float, float, float, float]:
        "计算外围数据 例如 margin padding border-radius"

        marginAll = self.calc(key, "0px")
        marginLen = len(marginAll)

        if marginLen == 1:
            return marginAll * 4
        elif marginLen == 2:
            return marginAll * 2
        elif marginLen == 3:
            return (*marginAll, marginAll[1])
        return marginAll

    def paste(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, left: float, top: float):
        "将内容粘贴在画布上"

        # 位移
        x = self.m3 + self.p3
        y = self.m0 + self.p0
        inline = 0
        # 背景颜色
        bg = Image.new('RGBA', (int(self.p3 + self.width + self.p1), int(self.p0 + self.height + self.p2)), self.style.get("background-color", "rgba(0,0,0,0)"))
        a = radiusMask(bg.getchannel("A"), self.outside("border-radius"))
        canvas.paste(bg, (int(left + self.m3), int(top + self.m0)), a)
        # 内容
        lm = 0
        for c in self.children:
            if c.position == "absolute":
                cleft, = c.calc("left", 0.0)
                ctop, = c.calc("top", 0.0)
                c.paste(canvas, draw, cleft, ctop)
            else:
                c.paste(canvas, draw, left + x, top + y + max(lm - c.m0, 0))
                if c.style.get("display", "block").startswith("inline"):
                    inline = max(inline, max(lm, c.m0) + c.p0 + c.height + c.p2)
                else:
                    y += inline + max(lm, c.m0) + c.p0 + c.height + c.p2
                    inline = 0
                lm = c.m2


class ImgTag(Tag):
    def __init__(self, data: dict, parent: Tag = None):
        self.src: str | Image.Image = ""
        super().__init__("img", data, parent)

    def __repr__(self):
        return "  " * self.depth + f'<img src="{self.src}" id="{self.id}" />'

    def setSize(self) -> float:
        if isinstance(self.src, str):
            res = httpx.get(self.src)
            data = BytesIO(res.content)
            img = Image.open(data)
        else:
            img = self.src
        self.height = img.height * self.width / img.width
        self.img = img.resize((int(self.width), int(self.height)), Image.LANCZOS).convert("RGBA")
        return self.height

    def paste(self, canvas: Image.Image, _: ImageDraw.ImageDraw, left: float, top: float):
        x = self.m3 + self.p3
        y = self.m0 + self.p0
        a = radiusMask(self.img.getchannel("A"), self.outside("border-radius"))
        canvas.paste(self.img, (int(left + x), int(top + y)), a)


class TextTag(Tag):
    def __init__(self, data: str, parent: Tag = None):
        self.tag = "text"
        self.text = data
        self.parent = parent
        self.depth = parent.depth + 1
        self.position = "static"
        self.style = dict()

        self.m0 = self.m1 = self.m2 = self.m3 = self.p0 = self.p1 = self.p2 = self.p3 = 0.0

    def __repr__(self):
        return "  " * self.depth + self.text

    @property
    def css(self):
        return ""

    def calcHeight(self, sentence):
        self.sentence += sentence + "\n"
        _, offset, _, h = self.font.getbbox(sentence)
        self.height += offset / 2 + h

    def outside(self, _: str):
        return 0.0, 0.0, 0.0, 0.0

    def setSize(self) -> float:
        fontpath = FontWeight(self.parent.style.get("font-weight", "Medium"))
        self.font = ImageFont.truetype(fontpath, int(self.parent.font_size), encoding="utf-8")
        self.sentence = ""
        self.height = 0

        sentence = ""
        for chn in self.text:
            if self.font.getlength(sentence + chn) > self.parent.width:
                self.calcHeight(sentence)
                sentence = chn
            else:
                sentence += chn
        else:
            if sentence != "":
                self.calcHeight(sentence)

        return self.height

    def paste(self, _: Image.Image, draw: ImageDraw.ImageDraw, left: float, top: float):
        draw.text((left, top), self.sentence, self.parent.style.get("color", "black"), self.font)


class createApp(Tag):
    def __init__(self, width: float, font_size: float = 16, depth: int = 0):
        self.width = width
        self.depth = depth
        self.font_size = font_size
        self.canvas = None

    def mount(self, config: dict = None, vue: str = None, fp: TextIOWrapper = None, path: str = None, data: dict = dict()):
        tp = template(data)
        if vue is not None:
            config = tp.loads(vue)
        elif fp is not None:
            config = tp.load(fp)
        elif path is not None:
            config = tp.file(path)
        assert config is not None, "config lost"
        self.html = self.makeTag(config)
        self.canvas = None
        return self

    def export(self, filepath: str = None):
        "导出图片"

        # 获取画布高度
        self.height = self.html.setSize()
        # 创建画布
        self.canvas = Image.new('RGBA', (int(self.width), int(self.height)), self.html.style.get("background-color", "#00000000"))
        # 创建画笔
        self.draw = ImageDraw.Draw(self.canvas)
        # 绘制
        self.html.paste(self.canvas, self.draw, 0, 0)
        # 保存画布
        if filepath is not None:
            self.canvas.save(filepath)

        return self

    def show(self):
        if self.canvas is None:
            self.export()
        self.canvas.show()
        return self

    def save(self, path: str):
        "导出 Vue"

        with open(path, "w+", encoding="utf-8") as fp:
            css = "\n\n".join(self.html.css)
            fp.write(
                f"<template>\n{self.html}\n</template>\n\n<style scoped>\n{css}\n</style>")

        return self
