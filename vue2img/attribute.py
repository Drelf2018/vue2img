import re
from inspect import isclass
from typing import Dict, List, Tuple, Type


def calcToFloat(expr: str, font_size: float = 16, compared_value: float = 0) -> float:
    """
    ### 对 calc() 运算 目前支持转换的单位 px em %

    expr: calc() 表达式

    font_size: 本节点字体大小

    compared_value: 相对值 例如 width 的相对值是父节点的 width

    参考 https://developer.mozilla.org/zh-CN/docs/Learn/CSS/Building_blocks/Values_and_units

    https://blog.csdn.net/weixin_48644617/article/details/123862697

    当你想用正则解决一个问题 你就有了两个问题
    """

    expr = expr.replace("px", "").replace("calc", "")

    for value in re.findall(u"[\d\.]+(?:em|%)", expr):
        value: str
        if value.endswith("em"):
            nv = float(value[:-2]) * font_size
            expr = expr.replace(value, str(nv))
        elif value.endswith("%"):
            nv = float(value[:-1]) * compared_value / 100
            expr = expr.replace(value, str(nv))

    try:
        result: float = eval(expr)  # 这里还是用 eval 方便啊 感觉没有安全隐患 除非你自己给自己的模板里加炸弹
        return result
    except Exception as e:
        raise Exception(f"{e}: 你传的 {expr} 是牛魔啊")


def setting(initial: str = "0px", inherited: bool = False, compared: Tuple[str] = None):
    "修改属性类初始值的装饰器"

    def wapper(cls):
        cls.initial = initial
        cls.inherited = inherited
        if compared is not None:
            cls.compared = compared
        return cls
    return wapper


class Attribute:
    "样式属性"
    
    initial = "0px"
    inherited = False
    compared = ("fontSize", "parent.width")

    def __init__(self, value: str = "initial"):
        """
        属性初始值判断 有点麻烦啊

        参考：https://blog.csdn.net/sinolover/article/details/109497752

        情况一：提供了 value 直接用 value
        
        情况二：未提供 value 不可继承用 initial
        
        情况三：未提供 value 可以继承用 inherit
        """

        self._value = None
        self.important = "!important" in value

        if value == "initial":
            if self.inherited:
                self.original = "inherit"
            else:
                self.original = self.initial
        else:
            self.original = value.replace("!important", "")

        self._expressions = self.split()

    def init(self):
        "再初始化"

        self.original = self.initial
        self._expressions = self.split()
        return self

    @property
    def unset(self) -> bool:
        "没有设置初始值"

        return self.original == self.initial or self.original == "inherit"

    @property
    def value(self) -> float:
        "用来给 _value 标注类型方便使用的"

        return self._value

    @property
    def expressions(self) -> Tuple[str]:
        "用来给 _expressions 标注类型方便使用的"

        return self._expressions

    @property
    def name(self):
        "属性名"

        s = self.__class__.__name__
        return s[0].lower() + s[1:]
    
    @classmethod
    def css(cls):
        "css 属性名"

        s = cls.__name__
        for chn in s:
            if "A" <= chn <= "Z":
                s = s.replace(chn, "-"+chn.lower())
        return s[1:]

    def __repr__(self) -> str:
        "打印"

        if self.value is None:
            return ""
        return str(self.value)

    def equal(self, *values: str) -> bool:
        "判断属性值是否为给定值之一"

        return self.original in values or self.value in values

    def inherit(self, value):
        "继承"

        self._value = value

    def completion(self, expr: List[str]) -> Tuple[str]:
        "补全表达式 例如 margin 可以填写 1-4 个参数"

        # 基础类默认至多一个 若有多个请继承类似 Attribute4 类
        el = len(expr)
        if el == 0:
            return "",
        else:
            return expr[0],

    def split(self):
        "分割 style 表达式"

        expr: List[str] = list()
        depth = 0  # 括号层数
        temp = ""  # 暂存含括号表达式

        for token in self.original.split(" "):
            if token == "":
                continue

            if "(" in token:
                depth += 1
            elif ")" in token:
                depth -= 1

            if depth == 0:
                expr.append(temp+token)
                temp = ""
            else:
                temp += token + " "

        return self.completion(expr)

    def transform(self, font_size: float = 16, compared_value: float = 0):
        "将表达式中 calc() rgb() 等函数转换为标准值"

        val, = self.expressions
        self._value = calcToFloat(val, font_size, compared_value)


class Attribute2(Attribute):
    "2 值属性"

    @property
    def value(self) -> Tuple[float, float]:
        return super().value

    @property
    def expressions(self) -> Tuple[str, str]:
        return super().expressions

    def completion(self, expr: List[str]) -> Tuple[str, str]:
        "补全 2 个参数"

        el = len(expr)
        if el == 0:
            return ("", "")
        elif el == 1:
            return tuple(expr * 2)
        else:
            return tuple(expr[:2])
        
    def transform(self, font_size: float = 16, compared_value: float = 0):
        values = [calcToFloat(v, font_size, compared_value) for v in self.expressions]
        self._value = tuple(values)


class Attribute4(Attribute2):
    "4 值属性"

    @property
    def value(self) -> Tuple[float, float, float, float]:
        return super().value

    @property
    def expressions(self) -> Tuple[str, str, str, str]:
        return super().expressions

    def completion(self, expr: List[str]) -> Tuple[str, str, str, str]:
        "补全 4 个参数"

        el = len(expr)
        if el == 0:
            return ("", "", "", "")
        elif el == 1:
            return tuple(expr * 4)
        elif el == 2:
            return tuple(expr * 2)
        elif el == 3:
            return (*expr, expr[1])
        else:
            return tuple(expr[:4])


class Attribute8(Attribute4):
    "8 值属性"

    @property
    def value(self) -> Tuple[float, float, float, float, float, float, float, float]:
        return super().value

    @property
    def expressions(self) -> Tuple[str, str, str, str, str, str, str, str]:
        return super().expressions

    def completion(self, expr: List[str]) -> Tuple[str, str, str, str, str, str, str, str]:
        "补全 8 个参数"

        if "/" in expr:
            pos = expr.index("/")
            return super().completion(expr[:pos]) + super().completion(expr[pos+1:])
        else:
            return super().completion(expr) * 2


class AttributeAll(Attribute):
    "不定值属性"

    @property
    def value(self) -> Tuple[float, ...]:
        return super().value

    @property
    def expressions(self) -> Tuple[str, ...]:
        return super().expressions

    def completion(self, expr: List[str]) -> Tuple[str, ...]:
        return tuple(expr)


@setting(compared=tuple())
class AttributeText(Attribute):
    "文本属性"

    @property
    def value(self) -> str:
        return super().value

    def transform(self):
        self._value, = self.expressions


@setting("16px", True, ("parent.fontSize",))
class FontSize(Attribute):
    def transform(self, parent_font_size: float = 16):
        super().transform(parent_font_size, parent_font_size)


class Padding(Attribute4):
    def transform(self, font_size: float = 16, compared_value: float = 0):
        super().transform(font_size, compared_value)
        self.top, self.right, self.bottom, self.left = self.value

    @property
    def side(self):
        "左右两侧"

        return self.left + self.right
    
    @property
    def tiandi(self):
        "天地"

        return self.top + self.bottom


class Margin(Padding): ...


@setting("auto", compared=("fontSize", "parent.width", "side"))
class Width(Attribute):    
    def transform(self, font_size: float = 16, compared_value: float = 0, side: float = 0):
        "当 width 为 auto 时值会设为父元素减去梓神 margin padding (border) 左右两侧"

        val, = self.expressions
        if val == "auto":
            self._value = compared_value - side
        else:
            self._value = calcToFloat(val, font_size, compared_value)


@setting("auto", compared=("fontSize", "parent.height"))
class Height(Attribute):
    def transform(self, font_size: float = 16, compared_value: float = 0):
        val, = self.expressions
        if val == "auto":
            self._value = None  # 见 `class Rectangle` 初始化函数处解释
        else:
            self._value = calcToFloat(val, font_size, compared_value)


@setting(compared=("fontSize", "width", "height"))
class BorderRadius(Attribute8):
    def transform(self, font_size: float = 16, width: float = 0.0, height: float = 0.0):
        if height is None:
            height = width
        valuesX = [calcToFloat(v, font_size, width) for v in self.expressions[:4]]
        valuesY = [calcToFloat(v, font_size, height) for v in self.expressions[4:]]
        self._value = tuple(valuesX + valuesY)
        self.topLeftX, self.topRightX, self.bottomRightX, self.bottomLeftX,self.topLeftY, self.topRightY, self.bottomRightY, self.bottomLeftY = self.value


@setting("", compared=("fontSize", "width", "gridGap"))
class GridTemplateColumns(AttributeAll):
    def transform(self, font_size: float = 0.0, width: float = 0.0, gridGap: Tuple[float] = (0.0, 0.0)):
        fr = 0
        static = 0
        values: List[str, float] = []
        for val in self.expressions:
            if val.endswith("fr"):
                fr += float(val[:-2])
                values.append(val)
            else:
                n = calcToFloat(val, font_size, width)
                static += n
                values.append(n)

        self.gridTotal = len(self.expressions)
        nw = width - static - (self.gridTotal - 1) * gridGap[0]

        for i in range(len(values)):
            v = values[i]
            if v.endswith("fr"):
                values[i] = nw * float(v[:-2]) / fr

        self._value = tuple(values)
        self.gridNum = 0

    def next(self, gridNum: int):
        return self.value[gridNum % self.gridTotal]


@setting(compared=("fontSize", "width", "height"))
class GridGap(Attribute2):
    def transform(self, font_size: float = 16, width: float = 0.0, height: float = 0.0):
        v0, v1 = self.expressions
        self.row = calcToFloat(v0, font_size, width)
        self.column = calcToFloat(v1, font_size, height)
        self._value = (self.row, self.column)


@setting("black", True)
class Color(AttributeText): ...


@setting("#00000000", True)
class BackgroundColor(AttributeText): ...


@setting("msyh", True)
class FontFamily(AttributeText): ...


@setting("block")
class Display(AttributeText): ...


@setting("none")
class Float(AttributeText): ...


@setting("static")
class Position(AttributeText): ...


class Top(Attribute): ...


class Left(Attribute): ...


def attribute_types(local: Dict[str, Type[Attribute]]):
    ATTRIBUTE_TYPES = {}
    for v in local.values():
        v: Attribute
        if not isclass(v):
            continue
        # 下面暂时不需要 除非在这里加了非 Attribute 类
        # if not issubclass(v, Attribute):
        #     continue
        ATTRIBUTE_TYPES[v.css()] = v

    def warpper(func):
        def inner(cmd: str) -> Attribute:
            "解析属性语句"

            name, value = cmd.split(":")
            attr = ATTRIBUTE_TYPES.get(name.strip())
            if attr is None:
                raise Exception(f"{name} 属性暂不支持")
            return attr(value=value.strip())
        return inner
    return warpper


@attribute_types(locals())
def makeAttribute(cmd: str) -> Attribute: ...