"""验证码内存存储，带 TTL 过期。

使用进程内 OrderedDict 保存验证码（键为 id，值为验证码与过期时间戳），
验证通过即弹出（一次性消费）。注意：内存存储不跨 worker 共享，多进程部署时
验证码会相互独立（AGENTS.md 已注明，属已知边界，勿当作 bug 修改）。
"""

import secrets
import time
from collections import OrderedDict

_MAX_SIZE = 100
_TTL = 300  # 5 minutes

_store: OrderedDict[str, tuple[str, float]] = OrderedDict()


def create(code: str) -> str:
    expire(True)
    cid = secrets.token_hex(16)
    _store[cid] = (code.upper(), time.time() + _TTL)
    if len(_store) > _MAX_SIZE:
        _store.popitem(last=False)
    return cid


def verify(cid: str, code: str) -> bool:
    expire(True)
    entry = _store.pop(cid, None)
    if entry is None:
        return False
    stored_code, expires = entry
    return time.time() < expires and stored_code == code.upper()


def expire(force_clear: bool = False):
    now = time.time()
    expired = [k for k, (_, t) in _store.items() if now > t]
    for k in expired:
        del _store[k]
