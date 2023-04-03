import json
from io import TextIOWrapper
from typing import Dict, List

from lxml import etree


def loads(vue: str, data: dict = dict()):
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
                    if k[0] == ":":
                        config[k[1:]] = data.get(v, "")
                    else:
                        config[k] = v
            return config
    
    return dfs(template.find("./*"))


def load(fp: TextIOWrapper, data: dict = dict()):
    return loads(fp.read(), data)


def file(path: str, data: dict = dict()):
    return load(open(path, "r+", encoding="utf-8"), data)
