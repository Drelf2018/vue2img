from typing import Dict, Tuple

from PIL import ImageFont


class FontManager:
    __fonts: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = dict()

    def __getitem__(self, key: Tuple[str, int]):
        if key not in self.__fonts:
            path, size = key
            path = path.replace("'", "").replace('"', '')
            try:
                self.__fonts[key] = ImageFont.truetype(path, size, encoding="utf-8")
            except Exception as e:
                raise Exception(f'{e}: "{path}"')
        return self.__fonts[key]

fontManager = FontManager()