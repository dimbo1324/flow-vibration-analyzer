"""Rate-limiter singleton for the API layer.

Set IVA_DISABLE_RATE_LIMIT=1 to disable limiting (useful in tests or local dev).
"""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_enabled = os.environ.get("IVA_DISABLE_RATE_LIMIT", "").lower() not in ("1", "true", "yes")

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
