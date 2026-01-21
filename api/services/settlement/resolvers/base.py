from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseResolver(ABC):
    """
    BaseResolver es el contrato obligatorio para TODOS los deportes.
    No contiene lógica deportiva.
    """

    sport: str

    def __init__(self, api_client):
        self.api_client = api_client

    @abstractmethod
    def fetch_event(self, event_id: int) -> Dict[str, Any]:
        """
        Obtiene el evento final desde API-SPORTS.
        Debe devolver el payload crudo.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_pick(self, pick: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recibe un pick del contrato y devuelve:

        {
            "result": "WIN" | "LOSS" | "VOID",
            "evidence": { ... }
        }
        """
        raise NotImplementedError
