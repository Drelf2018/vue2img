import re
from copy import deepcopy
from dataclasses import dataclass, field

from .attribute import *

stylePattern = re.compile(r"[^:|\n|;]+:[^;]+")


@dataclass
class Style:
    "样式表"
    
    fontSize: FontSize = field(default_factory=FontSize)
    margin: Margin = field(default_factory=Margin)
    padding: Padding = field(default_factory=Padding)
    width: Width = field(default_factory=Width)
    
    top: Top = field(default_factory=Top)
    left: Left = field(default_factory=Left)    
    height: Height = field(default_factory=Height)
    borderRadius: BorderRadius = field(default_factory=BorderRadius)
    
    gridGap: GridGap = field(default_factory=GridGap)
    gridTemplateColumns: GridTemplateColumns = field(default_factory=GridTemplateColumns)
    
    color: Color = field(default_factory=Color)
    float: Float = field(default_factory=Float)
    display: Display = field(default_factory=Display)
    position: Position = field(default_factory=Position)
    fontFamily: FontFamily = field(default_factory=FontFamily)
    backgroundColor: BackgroundColor = field(default_factory=BackgroundColor)

    @property
    def attributs(self):
        "所有属性"

        for name, attr in self.__dict__.items():
            attr: Attribute
            yield name, attr

    @property
    def inheritable(self):
        "可继承属性"

        for name, attr in self.attributs:
            if attr.value is not None:
                continue
            if not attr.inherited or attr.original != "inherit":
                continue
            yield name, attr

    @property
    def prewidth(self):
        "先找 width 相关属性"

        # 这个函数有点想废掉 因为我发现 attributs 返回的顺序就是定义的顺序
        # 也就是说可以修改变量的位置达到这个效果
        # 但是可能就不美观了
        pre = ["fontSize", "margin", "padding", "width"]
        for name in pre:
            if self[name].value is not None:
                continue
            yield name, self[name]
        for name, attr in self.attributs:
            if name in pre or attr.value is not None:
                continue
            yield name, attr

    @property
    def original(self):
        "原始值"

        sl = []
        for name, attr in self.attributs:
            sl.append(f"{name}={attr.original}")
        s = ", ".join(sl)
        return f"Style({s})"

    def __repr__(self):
        "计算值"

        sl = []
        for name, attr in self.attributs:
            if str(attr) != "":
                sl.append(f"{name}={attr}")
        s = ", ".join(sl)
        return f"Style({s})"

    def __getitem__(self, key: str) -> Attribute:
        return self.__dict__.get(key, None)

    def __setitem__(self, key: str, value: Attribute):
        self.__dict__[key] = value

    def get(self, key: str, value: str = ""):
        "获取属性"

        if self[key] is None:
            return value
        return self[key]

    def values(self, *keys: str, normal_index: int = -1):
        "获取多个属性值"

        vals = []
        for key in keys:
            if isinstance(key, str):
                if key.startswith("parent."):
                    vals.append(key.replace("parent.", ""))
                elif key == "side":
                    vals.append(self.margin.side + self.padding.side)
                elif key == "width":
                    if self.display.equal("grid") and normal_index != -1:
                        vals.append(self.gridTemplateColumns.next(normal_index))
                    else:
                        vals.append(self.width.value)
                elif self[key] is not None:
                    vals.append(self[key].value)
            else:
                vals.append(key)
        return tuple(vals)

    def inherit(self, parent_style: "Style", normal_index: int):
        "继承父属性"

        for name, attr in self.inheritable:
            attr.inherit(parent_style[name].value)  # 只继承值

        if self.position.equal("absolute"):
            normal_index = -1

        for name, attr in self.prewidth:
            args = self.values(normal_index=-1, *attr.compared)
            args = parent_style.values(normal_index=normal_index, *args)
            attr.transform(*args)

        return self

    def update(self, *latests: "Style"):
        "叠加属性值"

        for latest in latests:
            for name, attr in latest.attributs:
                if attr.unset:
                    continue
                if self[name].important and not attr.important:
                    continue
                self[name] = attr
        return self
    
    @classmethod
    def parse_style(cls, s: str):
        "解析字符串 style 为 `Style` 类型"
        
        style = cls()
        if s is not None:
            for cmd in stylePattern.findall(s.strip()):
                attr = makeAttribute(cmd)
                if attr is not None:
                    style[attr.name] = attr
        return style


@dataclass
class SpanStyle(Style):
    display: Display = Display("inline")


@dataclass
class TextStyle(SpanStyle): ...


@dataclass
class PStyle(Style):
    margin: Margin = Margin("1em 0px")


@dataclass
class H1Style(Style):
    fontSize: FontSize = FontSize("2em")
    margin: Margin = Margin("0.67em 0px")