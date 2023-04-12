import os
from typing import Set, Tuple

import jieba
import numpy as np
from PIL import Image, ImageDraw
from wordcloud import STOPWORDS, WordCloud

from .font import FontWeight

stopwords = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "stopwords.txt"
    )
)


def radiusMask(alpha: Image.Image, radius: Tuple[float], beta: float = 10):
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


def word2cloud(danmakus: str, mask: Image.Image, content: Set[str] = set()) -> Image.Image:
    # jieba 分词
    jieba.add_word('睡啄')
    sentence = "/".join(jieba.cut(danmakus))
    graph = np.array(mask)

    # 停用词
    if not content:
        content = set(line.strip() for line in open(stopwords, "r", encoding="utf-8").readlines())

    # 词云
    return WordCloud(
        font_path=FontWeight("Regular"),
        prefer_horizontal=1,
        collocations=False,
        background_color=None,
        mask=graph,
        stopwords=content | STOPWORDS,  
        mode="RGBA"
    ).generate(sentence).to_image()