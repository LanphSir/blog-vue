"""站点配置键的白名单校验规则。

只对已知键做格式校验；未知键直接放行，保证未来新增配置不会因校验表未更新
而阻塞保存。`PUT /admin/site/config` 会在写入前对整批配置逐项校验，任一非法
即整批 422 拒绝，避免"部分写入"造成配置不一致。
"""

import re

# 站点强调色只允许 #RGB 或 #RRGGBB 两种十六进制形式
_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

ALLOWED_BACKGROUNDS = {"none", "grid", "aurora", "dots", "topo", "geek", "line"}


def _check_int_range(value: str, low: int, high: int, label: str) -> str | None:
    try:
        number = int(value)
    except ValueError:
        return f"{label}必须是整数"
    if not low <= number <= high:
        return f"{label}必须在 {low}-{high} 之间"
    return None


def check_config_value(key: str, value: str) -> str | None:
    """Return an error message when the value is invalid, otherwise None."""
    if key == "site_accent_color" and value:
        if not _HEX_COLOR.match(value):
            return "主题强调色必须是 #RGB 或 #RRGGBB 格式"
    elif key == "sidebar_tag_count" and value:
        return _check_int_range(value, 1, 30, "标签云数量")
    elif key == "site_background" and value:
        if value not in ALLOWED_BACKGROUNDS:
            return "背景方案必须是 none/grid/aurora/dots/topo/geek/line 之一"
    return None
