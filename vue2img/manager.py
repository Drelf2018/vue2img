from typing import Dict, Tuple

from PIL import ImageFont

from .style import Style


class FontManager:
    "字体管理器"

    __fonts: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = dict()

    @classmethod
    def truetype(cls, key: Tuple[str, int]):
        "根据字体路径和字号获取字体"

        if key not in cls.__fonts:
            path, size = key
            path = path.replace("'", "").replace('"', '')
            size = int(size)
            try:
                cls.__fonts[key] = ImageFont.truetype(path, size, encoding="utf-8")
            except Exception as e:
                raise Exception(f'{e}: "{path}"')
        return cls.__fonts[key]

    @classmethod
    def from_style(cls, style: Style):
        "从样式获取字体"

        return cls.truetype(style.values("fontFamily", "fontSize"))