from dataclasses import dataclass, field
from io import BytesIO
from typing import List, Tuple, Union, overload

import httpx
from PIL import Image, ImageDraw

from .manager import fontManager
from .operation import radiusMask


@dataclass
class DOM:
    tagName: str
    parent: "DOM" = None
    style: dict = field(default_factory=dict)
    attribute: dict = field(default_factory=dict)

    def __post_init__(self):
        "初始化"

        # 梓元素
        self.__children: List[Union["DOM", str]] = list()

        # 定位
        self.position = self.style.get("position", "static")
        self.display = self.style.get("display", "block")
        self.__size = [0.0, 0.0]

        # 基础属性 先计算字号再计算宽度
        self.font_size, = self.calc("font-size")
        self.width, = self.calc("width")
        self.height, = self.calc("height", 0.0)
        self.bgColor = self.style.get("background-color", "rgba(0,0,0,0)")

        # 计算 margin padding
        self.m0, self.m1, self.m2, self.m3 = self.outside("margin")
        self.p0, self.p1, self.p2, self.p3 = self.outside("padding")

        # 定位子元素
        self.cx, self.cy = 0.0, 0.0

    @overload
    def append(self, text: str) -> None: 
        "尾部插入字符"

    @overload
    def append(self, element: "DOM") -> None:
        "尾部插入子节点"

    def append(self, child: Union["DOM", str]):
        "尾部插入子元素"

        if isinstance(child, str):
            child = TextDOM(parent=self, text=child)
        else:
            # 修正尺寸
            child.height += child.cy

            if child.tagName == "span":
                child.width = 0.0
                for _, dom in child.forEach("#text"):
                    child.width += dom.width

        if child.position != "absolute":
            height = child.m0 + child.p0 + child.height + child.p2 + child.m2
            if child.display.startswith("inline"):
                child.setSize(self.cx, self.height)
                self.cx += child.m3 + child.p3 + child.width + child.p1 + child.m1
                self.cy = max(height, self.cy)
            else:
                if self.cy != 0.0:
                    self.height += self.cy
                    self.cy = 0.0
                
                overlap = min(child.m0, self.lastMargin)
                child.setSize(0, self.height - overlap)
                self.height += height - overlap
                self.cx = 0.0

        self.__children.append(child)

    @property
    def children(self):
        return self.__children

    @property
    def lastMargin(self) -> float:
        if len(self.__children) == 0:
            return 0.0
        else:
            ele = self.__children[-1]
            if ele.display.startswith("inline"):
                return 0.0
            return ele.m2

    @property
    def inheritStyle(self) -> dict:
        return {
            "font-size": self.font_size,
            "font-family": self.style.get("font-family", "msyh"),
            "color": self.style.get("color", "black"),
            "background-color": self.bgColor
        }

    @property
    def size(self):
        return tuple(self.__size)
    
    def setSize(self, left: float = 0.0, top: float = 0.0):
        self.__size = [left, top]

    def forEach(self, tagName: str = "*"):
        "遍历"

        return enumerate([child for child in self.__children if tagName == "*" or child.tagName == tagName])
    
    def tree(self, depth: int = 0):
        "打印树形结构"

        print(" " * depth + f"DOM(tagName='{self.tagName}')")
        for _, child in self.forEach():
            if isinstance(child, str):
                print(" " * (depth + 1) + child)
            else:
                child.tree(depth + 1)

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
        """将内容粘贴在画布上

        left: 内容区相对图片左边距
        top: 内容区相对图片上边距
        """

        # 强制覆盖高度
        height, = self.calc("height", self.height)

        # 背景颜色
        bg = Image.new('RGBA', (int(self.p3 + self.width + self.p1), int(self.p0 + height + self.p2)), self.bgColor)
        a = radiusMask(bg.getchannel("A"), self.outside("border-radius"))
        canvas.paste(bg, (int(left - self.p3), int(top - self.p0)), a)

        # 内容
        for _, child in self.forEach():
            x, y = child.size
            cleft, = child.calc("left", 0.0)
            ctop, = child.calc("top", 0.0)
            if child.position == "absolute":
                ...
            elif child.position == "relative":
                cleft += left + x
                ctop += top + y
            else:
                cleft = left + x
                ctop = top + y
            child.paste(canvas, draw, cleft + child.m3 + child.p3, ctop + child.m0 + child.p0)


class ImgDOM(DOM):
    tagName: str = "img"

    def __post_init__(self):
        super().__post_init__()
        src = self.attribute.get("src")
        if isinstance(src, str):
            res = httpx.get(self.src)
            data = BytesIO(res.content)
            img = Image.open(data)
        else:
            img = src
        self.height = img.height * self.width / img.width
        self.img = img.resize((int(self.width), int(self.height)), Image.LANCZOS).convert("RGBA")

    def paste(self, canvas: Image.Image, _: ImageDraw.ImageDraw, left: float, top: float):
        a = radiusMask(self.img.getchannel("A"), self.outside("border-radius"))
        canvas.paste(self.img, (int(left), int(top)), a)


@dataclass
class TextDOM(DOM):
    text: str = ""
    tagName: str = "#text"

    def __post_init__(self):
        self.position = "static"
        self.display = "inline"
        self.max_width = self.parent.width
        self.m0 = self.m1 = self.m2 = self.m3 = self.p0 = self.p1 = self.p2 = self.p3 = 0.0

        # 分割文本
        fontpath = self.parent.style.get("font-family", "msyh")
        self.font = fontManager[fontpath, int(self.parent.font_size)]

        sentences = []
        self.height = 0.0
        temp = ""

        def inner(temp: str):
            sentences.append(temp)
            _, offset, _, h = self.font.getbbox(temp)
            return offset / 2 + h

        for chn in self.text:
            if self.font.getlength(temp + chn) > self.max_width:
                self.height += inner(temp)
                temp = chn
            else:
                temp += chn
        if temp != "":
            self.height += inner(temp)

        self.text = "\n".join(sentences)

        # 修正尺寸
        if len(sentences) == 1:
            self.width = self.font.getlength(self.text)
        else:
            self.width = self.parent.width

    def paste(self, _: Image.Image, draw: ImageDraw.ImageDraw, left: float, top: float):
        if self.parent.style.get("float") == "right":
            left += self.max_width - self.width
        draw.text((left, top), self.text, self.parent.style.get("color", "black"), self.font)


TYPES = {
    "img": ImgDOM,
}