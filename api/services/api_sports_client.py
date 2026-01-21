from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests

try:
    from services.env import get_env
    from services.api_sports_hosts import SPORT_BASE_URL
except ModuleNotFoundError:
    from api.services.env import get_env  # type: ignore
    from api.services.api_sports_hosts import SPORT_BASE_URL  # type: ignore


@dataclass(frozen=True)
class ApiSportsClient:
    """
    Cliente único para TODOS los productos de API-SPORTS.
    Regla: UNA sola key (API_SPORTS_KEY) + base_url por deporte.
    """
    sport: str
    timeout: int = 30

    def _base_url(self) -> str:
        base = SPORT_BASE_URL.get(self.sport)
        if not base:
            raise ValueError(f"Sport no soportado o no configurado: {self.sport}")
        return base.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        env = get_env()
        return {"x-apisports-key": env["API_SPORTS_KEY"], "Accept": "application/json"}

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self._base_url() + path
        r = requests.get(url, headers=self._headers(), params=params or {}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
