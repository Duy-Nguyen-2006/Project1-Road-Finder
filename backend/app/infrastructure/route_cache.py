from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

DEFAULT_ROUTE_CACHE_LIMIT = 1000


@dataclass
class RouteCache:
    limit: int = DEFAULT_ROUTE_CACHE_LIMIT

    def __post_init__(self) -> None:
        self._entries: OrderedDict[str, Any] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self._entries)
