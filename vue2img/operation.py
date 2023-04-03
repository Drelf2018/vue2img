from PIL import Image, ImageDraw


def radiusMask(alpha: Image.Image, *radius: float, beta: float = 10):
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