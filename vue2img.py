import json
from io import BytesIO
from typing import Dict, List, Tuple

import httpx
from lxml import etree
from PIL import Image, ImageDraw, ImageFont


def radiusMask(alpha: Image.Image, *radius: float, beta: float = 10):
    "给遮罩层加圆角"

    w, h = alpha.size
    # 圆角的位置
    position = [
        (0, 0),
        (int(w - radius[1]), 0),
        (int(w - radius[2]), int(h - radius[2])),
        (0, int(h - radius[3]))
    ]
    for i, r in enumerate(radius):
        # 这里扩大 beta 倍画完扇形又缩小回去是为了抗锯齿
        circle = Image.new('L', (int(beta * r), int(beta * r)), 0)  # 创建黑色方形
        draw = ImageDraw.Draw(circle)
        draw.pieslice(((0, 0), (int(2 * beta * r), int(2 * beta * r))), 180, 270, fill=255)  # 绘制白色扇形
        circle = circle.rotate(-90 * i).resize((int(r), int(r)), Image.LANCZOS)  # 旋转以及缩小
        alpha.paste(circle, position[i])
    return alpha


class Tag:
    def __init__(self, tag: str, data: dict, parent: "Tag" = None):
        # 节点信息
        self.tag = tag
        self.parent = parent
        self.depth = parent.depth + 1

        # 基础 style
        self.style = data.pop("style", {})
        try:
            self.position = self.style.get("position", "static")
        except:
            print(self)
        
        # 计算 先计算字号再计算宽度
        self.font_size, = self.calc(key="font-size")
        self.width, = self.calc(key="width")

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
        cs = ["#" + self.id +
              " {\n" + "\n".join([f"  {k}: {v};" for k, v in self.style.items()]) + "\n}"]
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

        lm = 0
        for c in self.children:
            h = c.setSize()
            if c.position == "absolute":
                continue
            self.height += max(lm, c.m0) + c.p0 + h + c.p2
            lm = c.m2
        else:
            self.height += lm

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
        # 背景颜色
        bg = Image.new('RGBA', (int(self.p3 + self.width + self.p1), int(self.p0 + self.height + self.p2)), self.style.get("background-color", "rgba(0,0,0,0)"))
        a = radiusMask(bg.getchannel("A"), *self.outside("border-radius"))
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
                y += max(lm, c.m0) + c.p0 + c.height + c.p2
                lm = c.m2


class ImgTag(Tag):
    def __init__(self, data: dict, parent: Tag = None):
        self.src = ""
        super().__init__("img", data, parent)

    def __repr__(self):
        return "  " * self.depth + f'<img src="{self.src}" id="{self.id}" />'
    
    def setSize(self) -> float:
        res = httpx.get(self.src)
        data = BytesIO(res.content)
        img = Image.open(data)
        self.height = img.height * self.width / img.width
        self.img = img.resize((int(self.width), int(self.height)), Image.LANCZOS).convert("RGBA")
        return self.height

    def paste(self, canvas: Image.Image, _: ImageDraw.ImageDraw, left: float, top: float):
        x = self.m3 + self.p3
        y = self.m0 + self.p0
        a = radiusMask(self.img.getchannel("A"), *self.outside("border-radius"))
        canvas.paste(self.img, (int(left + x), int(top + y)), a)


class TextTag(Tag):
    def __init__(self, data: str, parent: Tag = None):
        self.tag = "text"
        self.text = data
        self.parent = parent
        self.depth = parent.depth + 1
        self.position = "static"

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
        self.font = ImageFont.truetype(".\HarmonyOS_Sans_SC_Bold.ttf", int(self.parent.font_size), encoding="utf-8")
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
    
    def mount(self, config: dict):
        self.html = self.makeTag(config)
        return self
    
    def export(self, filepath: str = None):
        "导出图片"

        # 获取画布高度
        self.height = self.html.setSize()
        # 创建画布
        self.canvas = Image.new('RGBA', (int(self.width), int(self.height)), self.html.style.get("background-color", "white"))
        # 创建画笔
        self.draw = ImageDraw.Draw(self.canvas)
        # 绘制
        self.html.paste(self.canvas, self.draw, 0, 0)
        # 保存画布
        if filepath is not None:
            self.canvas.save(filepath)

        return self
    
    def saveAsVue(self, filepath: str):
        "导出 Vue"

        with open(filepath, "w+", encoding="utf-8") as fp:
            css = "\n\n".join(self.html.css)
            fp.write(f"<template>\n{self.html}\n</template>\n\n<style scoped>\n{css}\n</style>")
        
        return self


def read_template(filepath: str, data: dict = dict()):
    # 获取 vue 文本
    vue = open(filepath, "r+", encoding="utf-8").read()
    # 获取 style 和 template
    html: etree._Element = etree.HTML(vue)
    style: str = html.findtext("body/style")
    template: etree._Element = html.find("body/template")
    
    # 样式表
    stylesheet: Dict[int, Dict[str, str]] = dict()
    
    # 给每个节点设置 attr 标记
    nodes: List[etree._Element] = [template]
    for node in nodes:
        node_id = str(id(node))
        node.set("python", node_id)
        nodes += node.getchildren()
        stylesheet[node_id] = dict()
    
    def style2dict(s: str):
        "将字符串 style 转换为 dict"

        if s is None:
            return dict()
        content = '{"' + (s.replace("\n", "") + ";").replace(";;", ";").replace(":", '":"').replace(";", '","').strip()[:-2] + "}"
        json_style: Dict[str, str] = json.loads(content)
        return {k.strip(): v.strip() for k, v in json_style.items()}

    # 解析 style
    for item in style.split("}"):
        item_split = item.split("{")
        if len(item_split) != 2 or item_split[1].strip() == "":
            continue

        # 把 css 具体键值转换为 json 文本格式再解析成 dict
        calc_style = style2dict(item_split[1])
        
        # css 选择后将其更新在样式表里
        for ele in template.cssselect(item_split[0]):
            if isinstance(ele, etree._Element):
                stylesheet[ele.get("python")].update(calc_style)
    
    def dfs(node: etree._Element | str):
        if isinstance(node, str):
            return node.strip().replace(r"{{", r"{").replace(r"}}", r"}").format_map(data)
        elif isinstance(node, etree._Element):
            # 从样式表提取 style 并用内联 style 优先替换
            style = stylesheet[node.get("python")]
            style.update(style2dict(node.get("style")))
            # 标签名 style 和子元素
            config = {
                "tag": node.tag,
                "style": style,
                "children": list(filter(lambda s: s != "", map(dfs, node.xpath("./*|text()"))))
            }
            # 各种数据 例如 img 的 src
            for k, v in node.items():
                if k not in ["style", "python", "id", "class"]:
                    if k.startswith(":"):
                        config[k[1:]] = data.get(v, "")
                    else:
                        config[k] = v
            return config
    
    return dfs(template.find("./*"))


data = {
    "img_url": "https://yun.nana7mi.link/7mi.webp",
    "face": "https://i1.hdslb.com/bfs/face/86faab4844dd2c45870fdafa8f2c9ce7be3e999f.jpg@120w_120h_1c.webp"
}
config = read_template(".\Test.vue", data)
createApp(1000).mount(config).export().canvas.show()