"""生成验证码图片并返回 PNG 字节。

纯内存合成，无文件落盘：4 位随机字符绘制后加噪点/干扰线/旋转，最终序列化为
PNG 字节供接口直接返回。字符库刻意只用数字与大写字母，避免大小写难以辨识。
"""

import io
import random
import string

from PIL import Image, ImageDraw, ImageFont

from app.core.config import BASE_DIR

_WIDTH = 130
_HEIGHT = 44
_FONT_SIZE = 28
_CHARS = string.digits + string.ascii_uppercase

# 按平台依次尝试常见字体路径，全部缺失时回退到 PIL 默认字体（保证不崩）
_FONT_CANDIDATES = [
    BASE_DIR / "app" / "core" / "DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _load_font():
    for path in _FONT_CANDIDATES:
        p = path if isinstance(path, str) else str(path)
        try:
            return ImageFont.truetype(p, _FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


_font = _load_font()


def _noise_color(base: tuple[int, int, int], amount: int = 40):
    r, g, b = base
    r = max(0, min(255, r + random.randint(-amount, amount)))
    g = max(0, min(255, g + random.randint(-amount, amount)))
    b = max(0, min(255, b + random.randint(-amount, amount)))
    return (r, g, b)


def generate() -> tuple[str, bytes]:
    code = "".join(random.choices(_CHARS, k=4))

    img = Image.new("RGB", (_WIDTH, _HEIGHT), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    # Background noise lines
    for _ in range(random.randint(4, 7)):
        x1 = random.randint(0, _WIDTH)
        y1 = random.randint(0, _HEIGHT)
        x2 = random.randint(0, _WIDTH)
        y2 = random.randint(0, _HEIGHT)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=_noise_color((200, 200, 210), 30),
            width=random.randint(1, 2),
        )

    # Characters with slight rotation and spacing
    total_w = 0
    for ch in code:
        c_img = Image.new("RGBA", (_FONT_SIZE + 4, _FONT_SIZE + 4), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(c_img)
        c_draw.text((2, 0), ch, fill=_noise_color((50, 60, 120), 40), font=_font)
        c_img = c_img.rotate(random.uniform(-25, 25), expand=1, fillcolor=(0, 0, 0, 0))
        img.paste(c_img, (total_w + random.randint(6, 10), random.randint(4, 10)), c_img)
        total_w += _FONT_SIZE - 4

    # Foreground dots
    for _ in range(random.randint(30, 60)):
        draw.point(
            (random.randint(0, _WIDTH), random.randint(0, _HEIGHT)),
            fill=_noise_color((150, 160, 180), 40),
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return code, buf.getvalue()
