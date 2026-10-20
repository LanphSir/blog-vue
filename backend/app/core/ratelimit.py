"""评论提交限流（进程内内存实现，同 captcha.py 模式）。

按客户端 IP 限制评论频率：COMMENT_RATE_WINDOW 秒内最多 1 条、每日 COMMENT_RATE
_DAILY 条。dict 记录每 IP 的最近提交时间与当日计数（跨天自动重置）。注意与验证
码存储同样的边界：SQLite 单 worker 部署下无碍，多 worker 时各自独立（AGENTS.md
已注明，非 bug）。
"""

import time

COMMENT_RATE_WINDOW = 30  # 秒/条
COMMENT_RATE_DAILY = 20  # 条/天

# ip -> (最近提交时间, 当日计数, 计数所属日期序号)
_hits: dict[str, tuple[float, int, int]] = {}


def check_and_record(ip: str) -> str | None:
    """允许则记录本次并返回 None；超限返回提示文案。"""
    now = time.time()
    day = int(now // 86400)
    last, count, last_day = _hits.get(ip, (0.0, 0, day))
    if last_day != day:
        last, count = 0.0, 0
    if now - last < COMMENT_RATE_WINDOW:
        return "评论太快了，请稍后再试"
    if count >= COMMENT_RATE_DAILY:
        return "今日评论次数已达上限，请明天再来"
    _hits[ip] = (now, count + 1, day)
    if len(_hits) > 10000:  # 粗粒度防膨胀
        for stale in sorted(_hits, key=lambda k: _hits[k][0])[:2000]:
            _hits.pop(stale, None)
    return None


def reset() -> None:
    """测试用：清空计数。"""
    _hits.clear()
