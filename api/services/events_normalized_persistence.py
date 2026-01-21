import json
from pathlib import Path
from typing import List, Dict

from services.events_normalizer_service import normalize_football_events


def persist_normalized_football_events(date: str) -> dict:
    """
    Ejecuta la normalización de eventos de fútbol y persiste el resultado
    en data/events/YYYY-MM-DD/football_normalized.json.

    - Si el archivo ya existe, NO se recalcula (bloqueo diario).
    - Devuelve metadata de ejecución.
    """

    base_path = Path("data/events") / date
    base_path.mkdir(parents=True, exist_ok=True)

    output_file = base_path / "football_normalized.json"

    if output_file.exists():
        return {
            "status": "skipped",
            "reason": "already_exists",
            "file": str(output_file),
        }

    normalized_events: List[Dict] = normalize_football_events(date)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normalized_events, f, ensure_ascii=False, indent=2)

    return {
        "status": "created",
        "events": len(normalized_events),
        "file": str(output_file),
    }
