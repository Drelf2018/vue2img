from io import TextIOWrapper

from PIL import Image, ImageDraw

from .dom import DOM
from .template import template


class createApp:
    def __init__(self, width: float, font_size: float = 16):
        self.width = width
        self.font_size = font_size

    def mount(self, vue: str = None, fp: TextIOWrapper = None, path: str = None, data: dict = dict()):
        self.canvas = None

        tp = template(DOM("body", style={"width": self.width, "font-size": self.font_size}), data)
        if vue is not None:
            self.dom = tp.loads(vue)
        elif fp is not None:
            self.dom = tp.load(fp)
        elif path is not None:
            self.dom = tp.file(path)
        assert self.dom is not None, "dom lost"

        return self

    def export(self, filepath: str = None):
        "导出图片"

        # 创建画布
        self.canvas = Image.new('RGBA', (int(self.width), int(self.dom.height)), "#00000000")
        # 创建画笔
        self.draw = ImageDraw.Draw(self.canvas)
        # 绘制
        self.dom.paste(self.canvas, self.draw, 0, 0)
        # 保存画布
        if filepath is not None:
            self.canvas.save(filepath)

        return self

    def show(self):
        if self.canvas is None:
            self.export()
        self.canvas.show()
        return self