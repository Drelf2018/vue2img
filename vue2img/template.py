import re
from copy import deepcopy
from io import TextIOWrapper
from typing import List

from lxml import etree

from .dom import DOM, TYPES

stylePattern = re.compile(r"[^:|\n|;]+:[^;]+")
varsPattern = re.compile(r"{{(.*?)}}")


def style2dict(s: str):
    "将字符串 style 转换为 dict"
    
    style = dict()
    if s is not None:
        for cmd in stylePattern.findall(s.strip()):
            cmd: str
            k, v = cmd.split(":")
            style[k.strip()] = v.strip()
    return style


class styleSheet:
    def __init__(self, key: str = "python"):
        self.key = key
        self.__dict = dict()

    def set_element_id(self, ele: etree._Element):
        "设置元素编号"

        eid = str(id(ele))
        ele.set(self.key, eid)

        self.__dict[eid] = style2dict(ele.get("style"))
        return eid

    def __get_element_id(self, ele: etree._Element):
        "获取元素编号"

        return ele.get(self.key)

    def set(self, ele: etree._Element, style: dict):
        "设置"

        eid = self.__get_element_id(ele)
        old = self.__dict.get(eid, dict())
        style = deepcopy(style)
        style.update(old)
        self.__dict[eid] = style

        return style


class template:
    "模板"

    def __init__(self, root: DOM, data: dict = dict()):
        # 额外数据
        self.data = data

        # 样式表
        self.stylesheet = styleSheet()

        # 根节点
        self.root = root

    def __dfs(self, node: etree._Element | str, parent: DOM) -> None:
        if isinstance(node, str):
            for var in varsPattern.findall(node):
                var: str
                node = node.replace("{{" + var + "}}", str(self.data.get(var.strip())))
            node = node.strip()
            if node != "":
                parent.append(node)
            return node
        elif isinstance(node, etree._Element):
            # 各种数据 例如 img 的 src
            attr = dict()
            for k, v in node.items():
                if k not in ["style", "id", "class", self.stylesheet.key]:
                    if k[0] == ":":
                        attr[k[1:]] = self.data.get(v, "")
                    else:
                        attr[k] = v

            style = self.stylesheet.set(node, parent.inheritStyle)
            me = TYPES.get(node.tag, DOM)(node.tag, parent, style, attr)
            
            for child in node.xpath("./*|text()"):
                self.__dfs(child, me)
            
            parent.append(me)

    def loads(self, vue: str):
        "直接读取模板字符串"

        # 获取 style 和 template
        html: etree._Element = etree.HTML(vue)
        self.template: etree._Element = html.find("body/template")
        self.style: str = re.sub(r"/\*.*?\*/", "", html.findtext("body/style"))
        
        # 给每个节点设置 attr 标记
        nodes: List[etree._Element] = [self.template]
        for node in nodes:
            nodes += node.getchildren()
            self.stylesheet.set_element_id(node)

        # 解析 style
        for item in self.style.split("}"):
            item_split = item.split("{")
            if len(item_split) != 2 or item_split[1].strip() == "":
                continue

            # 把 css 具体键值转换为 json 文本格式再解析成 dict
            calc_style = style2dict(item_split[1])
            
            # css 选择后将其更新在样式表里
            for ele in self.template.cssselect(item_split[0]):
                if isinstance(ele, etree._Element):
                    self.stylesheet.set(ele, calc_style)
        
        for ele in self.template.xpath("./*|text()"):
            self.__dfs(ele, self.root)
        
        return self.root

    def load(self, fp: TextIOWrapper):
        "从阅读器读取，阅读器须具有 fp.read()"

        return self.loads(fp.read())

    def file(self, path: str):
        "从文件读取"

        return self.load(open(path, "r+", encoding="utf-8"))
