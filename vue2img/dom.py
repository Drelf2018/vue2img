from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Type, Union

import httpx
from PIL import Image, ImageDraw

from .manager import fontManager
from .operation import radiusMask
from .style import *


@dataclass
class Rectangle:
    """
    节点矩形

    x, y: 左上角绝对坐标

    top, left: 相对原始位置的偏移

    width, height: 矩形长宽

    offsetX, offsetY: 左上角原本位置相对父元素左上角偏移量
    
    也就是正常情况下的坐标点 如果是 relative 在贴最终位置的时候要用这个点加 top, left
    """

    dom: "DOM" = None

    top: float = 0.0
    left: float = 0.0
    width: float = 0.0
    height: float = None

    def __post_init__(self):
        if self.dom is not None:
            style = self.dom.style

            self.lastMargin = 0.0  # 最后一个子元素的下 margin
            self.margin = style.margin
            self.padding = style.padding
            self.position = style.position

            self.__x = self.__y = None
            if self.position.equal("absolute"):
                self.__x = self.left
                self.__y = self.top

        self.height_read_only = self.height
        self.height = 0.0

    @property
    def finalHeight(self):
        "最终高度 如果有初始值则不返回自适应出的高度"

        if self.height_read_only is not None:
            return self.height_read_only
        return self.height

    @property
    def background(self) -> "Rectangle":
        "背景矩形 需要考虑 padding"

        return Rectangle(
            top=self.y - self.padding.top,
            left=self.x - self.padding.left,
            width=self.width + self.padding.side,
            height=self.finalHeight + self.padding.tiandi
        )

    @property
    def xy(self):
        "什么希侑"

        return int(self.x), int(self.y)

    @property
    def x(self):
        if self.dom is None:
            return self.left
        if self.dom.parentNode is None:
            return 0.0
        if self.__x is None:
            self.__x = self.dom.parentNode.content.x + self.offsetX + self.left
        return self.__x

    @property
    def y(self):
        if self.dom is None:
            return self.top
        if self.dom.parentNode is None:
            return 0.0
        if self.__y is None:
            self.__y = self.dom.parentNode.content.y + self.offsetY + self.top
        return self.__y

    @property
    def size(self):
        return int(self.width), int(self.finalHeight)

    @classmethod
    def init(cls, dom: "DOM"):
        "初始化矩形"

        # 这里调用了 `dom.style` 实际上起到了生成最终样式的作用
        # 详见 dom.style 定义处
        top, left, width, height = dom.style.values("top", "left", "width", "height")
        dom.content = cls(
            dom=dom,
            top=top,
            left=left,
            width=width,
            height=height
        )

    def set_offset(self, offsetX: float = 0.0, offsetY: float = 0.0):
        "设置元素偏移"

        self.offsetX = offsetX
        self.offsetY = offsetY
        return self

    def heighten(self, height: float):
        "自适应高度"

        self.height += height

    def append(self, child: "Rectangle"):
        "添加子元素矩形"

        # 参考: https://blog.csdn.net/iefreer/article/details/50708348
        if child.position.equal("absolute"):
            return

        overlap = max(0, child.margin.top - self.lastMargin)  # margin 重叠
        child.set_offset(child.margin.left + child.padding.left, self.height + overlap + child.padding.top)
        self.heighten(overlap + child.padding.tiandi + child.finalHeight + child.margin.bottom)
        self.lastMargin = child.margin.bottom


class DOM:
    tagStyle: Style = Style()
    
    def __init__(self, inner_style: Style = Style()):
        # 节点
        self.childNodes: List[DOM] = list()
        self.parentNode: Optional[DOM] = None
        self.pending_nodes: List[DOM] = list()
        self.next_node: Optional[DOM] = None
        self.previous_node: Optional[DOM] = None
        
        # 属性
        self.attributes: Dict[str, str] = dict()
        
        # 在父节点的非 absolute 子节点中序号
        self.normal_index = -1
        # 子元素中非 absolute 子节点个数
        self.normal_total = 0
        
        # 内容区位置矩形
        self.content: Optional[Rectangle] = None

        # 样式
        self.inner_style = inner_style
        self.id_style = Style()
        self.class_style = Style()
        self.tag_style = Style()
        self.__ComputedStyle = None

    @property
    def tagName(self):
        return self.__class__.__name__.replace("DOM", "").lower()

    @property
    def children(self):
        "子节点"

        return filter(lambda dom: dom.tagName != "text", self.childNodes)

    @property
    def nextSibling(self):
        "下一个兄弟节点"

        if self.parentNode is None:
            return None
        if self.next_node is None:
            childList = self.parentNode.childNodes
            pos = childList.index(self)
            if pos == len(childList) - 1:
                return None
            self.next_node = childList[pos + 1]
        return self.next_node

    @property
    def previousSibling(self):
        "前一个兄弟节点"

        if self.parentNode is None:
            return None
        if self.previous_node is None:
            childList = self.parentNode.childNodes
            pos = childList.index(self)
            if pos == 0:
                return None
            self.previous_node = childList[pos - 1]
        return self.previous_node

    @property
    def style(self):
        """
        获取计算样式
        
        初始状态 `self.__ComputedStyle is None`

        所有样式叠加完成后调用就会计算最终样式
        """

        if self.__ComputedStyle is None:
            self.__ComputedStyle = self.setComputedStyle()
        return self.__ComputedStyle

    def setComputedStyle(self) -> Style:
        "计算最终样式"

        return deepcopy(self.tagStyle).update(
            self.tag_style,
            self.class_style,
            self.id_style,
            self.inner_style
        ).inherit(self.parentNode.style, self.parentNode.normal_total)

    def __repr__(self):
        attr_text = ""
        for k, v in self.attributes.items():
            attr_text += f" {k}"
            if v != "":
                attr_text += f"={v}"
        return f"<{self.tagName}{attr_text} index={self.normal_index}>"

    def contain(self, *keys: Tuple[str]):
        "返回属性"

        for key in keys:
            if key in self.attributes:
                return self.attributes[key]
        return None

    def insert(self, node: "DOM"):
        "简易插入"

        if node is None:
            return
        node.parentNode = self
        self.childNodes.append(node)

    def insert_true_node(self, latest_node: Optional["DOM"] = None):
        """
        遍历判断 插入真等待节点 待部署为空则返回
        
        latest_node: v-else 节点
        """

        if len(self.pending_nodes) == 0:
            return
        node0 = self.pending_nodes.pop(0)
        if bool(node0.attributes["v-if"]):
            return self.insert(node0)
        while len(self.pending_nodes):
            node = self.pending_nodes.pop(0)
            if bool(node.attributes["v-else-if"]):
                return self.insert(node)
        self.insert(latest_node)

    def pending(self, node: "DOM"):
        "尾部插入等待节点"

        self.pending_nodes.append(node)

    def append(self, child: Union["DOM", str]):
        """
        尾部插入子元素
        
        插入新元素前自动检查是否还有剩余待插入元素

        即自动运行 `self.insert_true_node()`
        """

        self.insert_true_node()

        if isinstance(child, str):
            self.childNodes.append(TextDOM(self, child))
        elif isinstance(child, DOM):
            self.insert(child)

    def paste(self, canvas: Image.Image, draw: ImageDraw.ImageDraw):
        "将内容粘贴在画布上"

        # 背景颜色
        background = self.content.background
        bg = Image.new("RGBA", background.size, self.style.backgroundColor.value)
        # 虽然 borderRadius 已经是 8 值属性了 但是 radiusMask 目前只支持四个参数 问就是我懒
        a = radiusMask(bg.getchannel("A"), self.style.borderRadius.value[:4])
        canvas.paste(bg, background.xy, mask=a)


class ImgDOM(DOM):
    "图片节点"

    def resize(self, width: int, height: Optional[int] = None):
        "缩放图片"

        height = int(height) if height is not None else int(width * self.img.height / self.img.width)
        width = int(width)
        if self.img.width != width or self.img.height != height:
            self.img = self.img.resize((width, height), Image.LANCZOS).convert("RGBA")

    def fetch_image(self):
        "获取图片"

        src = self.attributes.get("src")
        if isinstance(src, str):
            res = httpx.get(src)
            data = BytesIO(res.content)
            img = Image.open(data)
        else:
            img: Image.Image = src

        self.img = img

        self.resize(*self.style.values("width", "height"))
        self.content = Rectangle(
            dom=self,
            top=self.style.top.value,
            left=self.style.left.value,
            width=self.img.width,
            height=self.img.height
        )

    def paste(self, canvas: Image.Image, _: ImageDraw.ImageDraw):
        a = radiusMask(self.img.getchannel("A"), self.style.borderRadius.value[:4])
        canvas.paste(self.img, self.content.xy, a)


class TextDOM(DOM):
    "文字节点"

    def __init__(self, parentNode: DOM, text: str = ""):
        super().__init__()
        self.text = text
        self.parentNode = parentNode

    def set_size(self):
        "根据最大限制宽度切割文本"

        # 获取书写区域
        self.inner = self.parentNode.content
        self.max_width = self.inner.width

        # 分割文本
        fontpath = self.parentNode.style.fontFamily.value
        self.font = fontManager[fontpath, int(self.parentNode.style.fontSize.value)]

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
            self.width = self.max_width
        
        self.content = Rectangle(dom=self, width=self.width, height=self.height)

    @property
    def size(self):
        "获取大小"

        return int(self.width), int(self.height)

    def __repr__(self):
        return self.text

    def paste(self, _: Image.Image, draw: ImageDraw.ImageDraw):
        left, top = self.content.xy
        # if self.parentNode.style.float.equal("right"):
        #     left += self.max_width - self.width
        draw.text((left, top), self.text, self.parentNode.style.color.value, self.font)


class BodyDOM(DOM):
    def setComputedStyle(self) -> Style:
        self.inner_style.fontSize.transform(16)
        self.inner_style.width.transform(self.inner_style.fontSize.value)
        for _, attr in self.inner_style.attributs:
            if attr.unset:
                attr.init().transform(*self.inner_style.values(*attr.compared))
        return self.inner_style


class TemplateDOM(BodyDOM): ...


class DivDOM(DOM): ...


class SpanDOM(DOM):
    tagStyle = SpanStyle()


class PDOM(DOM):
    tagStyle: PStyle = PStyle()


class H1DOM(DOM):
    tagStyle: H1Style = H1Style()


def dom_types(local: Dict[str, Type[DOM]]):
    DOM_TYPES = {k.replace("DOM", "").lower(): v for k, v in local.items() if k.endswith("DOM")}
    def warpper(func):
        def inner(tagName: str, inner_style: Style = None):
            "通过 tagName 找对应类"

            return DOM_TYPES.get(tagName, DOM)(inner_style)
        return inner
    return warpper


@dom_types(locals())
def makeDOM(tagName: str, inner_style: Style = None) -> DOM: ...