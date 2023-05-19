import re
from io import TextIOWrapper
from typing import Dict, List, Optional, Union

from lxml.etree import HTML
from lxml.etree import _Element as Element

from .dom import DOM, BodyDOM, ImgDOM, Rectangle, TextDOM, makeDOM
from .style import Style
from .util import Travel, bfs, dfs

varsPattern = re.compile(r"{{(.*?)}}")


class Template:
    "模板"

    width: str = "800px"
    font_size: str = "16px"

    def __init__(self, vue: str = None, fp: TextIOWrapper = None, path: str = None, *args, **kwargs):
        "自动加载 `data()` 数据"

        self.__data = self.data(*args, **kwargs)
        self.__key = self.get("key", "dom")
        self.__doms: Dict[str, DOM] = dict()

        if vue is not None:
            self.loads(vue)
        elif fp is not None:
            self.load(fp)
        elif path is not None:
            self.file(path)

    def data(self, *args, **kwargs):
        return {
            "name": "App",
            "key": "dom"
        }

    def get(self, key: str, value: str = ""):
        "获取 `data()` 值"

        return self.__data.get(key, value)

    def dom(self, ele: Optional[Element]) -> Union[None, DOM, BodyDOM]:
        "获取对应节点 不存在会新建"

        if ele is None:
            return None

        did = ele.get(self.__key)
        if did is None:
            # 解析样式
            plain: str = ele.get("style")
            style = Style.parse_style(plain)
            dom = makeDOM(ele.tag, inner_style=style)

            # 解析属性
            for k, v in ele.items():
                k: str
                v: str
                if k != "style":
                    if k[0] == ":":
                        dom.attributes[k[1:]] = self.get(v)
                    elif k in ["v-if", "v-else-if"]:
                        dom.attributes[k] = self.get(v)
                    elif k == "v-for":
                        # 你猜我什么时候支持这个命令
                        ...
                    else:
                        dom.attributes[k] = v
            
            # 保存节点
            did = str(id(dom))
            ele.set(self.__key, did)
            self.__doms[did] = dom

        return self.__doms.get(did)        

    def cssselect(self, expr: str, limit: int = -1):
        """
        ### css 选择器
        
        limit: 最大返回节点数 负数返回所有
        """

        for ele in self.template.cssselect(expr):
            if limit == 0:
                # 我去 我是天才 初始值设为 -1 
                # 怎么减都不会等于零 变相获取全部返回值
                continue
            if isinstance(ele, Element):
                dom = self.dom(ele)
                if dom is not None:
                    yield dom
                    limit -= 1

    def replace(self, s: str):
        "替换文字"

        for var in varsPattern.findall(s):
            var: str
            s = s.replace("{{" + var + "}}", str(self.get(var.strip())))
        return s.strip()

    def loads(self, vue: str) -> DOM:
        "直接读取模板字符串"

        # 获取 template script style
        html: Element = HTML(vue)
        self.template: Element = html.find("body/template")
        self.script: str = html.findtext("body/script")
        self.style: str = re.sub(r"/\*.*?\*/", "", html.findtext("body/style"))

        # 新建 dom 树根节点
        self.template.set("style", f"width: {self.width};font-size: {self.font_size};")
        self.root: BodyDOM = self.dom(self.template)

        @bfs(self.template, lambda node: list(node.xpath("./*|text()")))
        class _(Travel):
            "利用 `etree._Element` 构建 `DOM` 树"

            # 当出现判断语句 v-if v-else-if 时
            # 把该等待节点存进 parentNode.pending_nodes 列表
            # 等待以下情况出现时再对这个列表进行操作
            # 1. 带有 v-else 节点出现
            # 2. 不带判断语句节点出现 包括文字节点
            # 3. 出现上述情况前父节点闭合了 通过 postorder() 解决

            @staticmethod
            def preorder(ele: Union[Element, str], depth: int, parent: Element):
                "建树"

                if parent is None:
                    return
                parentNode = self.dom(parent)
                if isinstance(ele, Element):
                    dom = self.dom(ele)
                    if dom.contain("v-if", "v-else-if") is not None:
                        parentNode.pending(dom)
                    elif dom.contain("v-else") is not None:
                        parentNode.insert_true_node(dom) # 出现 v-else
                    else:
                        parentNode.append(dom) # 一般节点
                else:
                    text = self.replace(ele)
                    if text != "":
                        parentNode.append(text) # 文字节点
                    return False  # 这里为何返回 False 见 util.bfs 定义

            @staticmethod
            def postorder(ele: Union[Element, str], depth: int, parent: Element):
                "处理闭合节点"

                if ele is None:
                    return
                self.dom(ele).insert_true_node()

        # 解析 style
        for item in self.style.split("}"):
            item_split = item.split("{")
            if len(item_split) != 2 or item_split[1].strip() == "":
                continue

            # 分析选择器类型
            query = item_split[0].strip().split(" ")[-1]
            style = Style.parse_style(item_split[1])
            for dom in self.cssselect(item_split[0].strip()):
                if query.startswith("#"):
                    dom.id_style.update(style)
                elif query.startswith("."):
                    dom.class_style.update(style)
                else:
                    dom.tag_style.update(style)

        @dfs(self.root)
        class _(Travel):
            "合并 `Style` 树、生成元素位置矩形"

            @staticmethod
            def preorder(dom: DOM, depth: int, parent: DOM) -> Optional[bool]:
                "在构建元素矩形同时生成元素最终样式 详见 `Rectangle.init()`"

                if isinstance(dom, TextDOM):
                    dom.set_size()
                elif isinstance(dom, ImgDOM):
                    dom.fetch_image()
                else:
                    Rectangle.init(dom)

            @staticmethod
            def postorder(dom: DOM, depth: int, parent: DOM) -> Optional[bool]:
                "设置矩形偏移"

                if parent is not None:
                    parent.content.append(dom.content)

        return self.root

    def load(self, fp: TextIOWrapper):
        "从阅读器读取，阅读器须具有 fp.read()"

        return self.loads(fp.read())

    def file(self, path: str):
        "从文件读取"

        return self.load(open(path, "r+", encoding="utf-8"))
