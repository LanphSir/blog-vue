"""Simple in-memory captcha store with TTL."""

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
