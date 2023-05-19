from dataclasses import dataclass
from typing import Optional, List

from PIL import Image, ImageDraw

from .util import bfs, Travel
from .dom import DOM
from .template import Template


def image(width: float = 500, height: float = 1000, background_color: str = "#00000000"):
    return Image.new("RGBA", (int(width), int(height)), background_color)


class Plugin:
    def install(self, app: "createApp"): ...


@dataclass
class createApp:
    App: Template

    def use(self, plugin: Plugin):
        "装模作样在 use"

        plugin.install(self)
        return self

    def mount(self, canvas: Optional[Image.Image] = None):
        "绑定图片"

        content = self.App.root.content
        self.canvas = canvas if canvas is not None else image(width=content.width, height=content.height)
        return self

    def export(self, fp: str = None):
        "导出图片"

        # 创建画笔
        self.draw = ImageDraw.Draw(self.canvas)

        # 绘制
        @bfs(self.App.root)
        def _(dom: DOM, depth: int, parent: DOM):
            dom.paste(self.canvas, self.draw)

        # 保存画布
        if fp is not None:
            self.canvas.save(fp, format="png")

        return self

    @property
    def show(self):
        "展示图片"

        self.export()
        self.canvas.show()

        return self