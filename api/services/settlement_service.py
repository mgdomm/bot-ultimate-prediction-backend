from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Union, Optional

from utils.football_results import get_football_result
from services.safe_call import safe_call
from utils.other_sports_results import get_other_sport_result
from utils.bet_evaluator import evaluate_bet
from services.contract_service import normalize_bet

DATA_DIR = "data"
SETTLEMENT_LOG = os.path.join("logs", "settlement.log")


def load_json(path: str) -> Union[Dict, List]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _append_log(obj: Dict):
    os.makedirs(os.path.dirname(SETTLEMENT_LOG), exist_ok=True)
    line = json.dumps(
        {"timestamp": datetime.utcnow().isoformat(), **obj},
        ensure_ascii=False,
    )
    with open(SETTLEMENT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _is_football_sport(s: str) -> bool:
    x = (s or "").strip().lower()
    return "futbol" in x or "fútbol" in x or x in {"football", "soccer"}


def _iter_bets(payload: Dict):
    for key in ("classic", "parlay"):
        lst = payload.get(key)
        if isinstance(lst, list):
            for i, b in enumerate(lst):
                if isinstance(b, dict):
                    yield lst, i, b


def collect_pending_bets() -> List[Tuple[str, str]]:
    pending = []
    if not os.path.exists(DATA_DIR):
        return pending

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, filename)
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue

        for _lst, _i, bet in _iter_bets(payload):
            if bet.get("result") is None and isinstance(bet.get("id"), str):
                pending.append((path, bet["id"]))

    return pending


def _find_bet(payload: Dict, bet_id: str):
    for lst, i, bet in _iter_bets(payload):
        if bet.get("id") == bet_id:
            return lst, i, bet
    return None


def settle_all_pending_bets() -> Dict:
    pending = collect_pending_bets()
    if not pending:
        return {"status": "ok", "message": "no pending bets"}

    settled = 0

    for source_path, bet_id in pending:
        payload = load_json(source_path)
        found = _find_bet(payload, bet_id)
        if not found:
            continue

        container, idx, bet = found

        sport = bet.get("sport", "")
        if _is_football_sport(sport):
            event_result = safe_call(lambda: get_football_result(bet), name='football_api')
        else:
            event_result = safe_call(lambda: get_other_sport_result(bet), name='other_sports_api')

        if event_result is None:
            continue

        final_result = evaluate_bet(bet, event_result)

        bet["result"] = final_result
        bet["status"] = "settled"

        normalized, errs = normalize_bet(bet, bet_type=bet.get("type"), default_stake=50.0)
        if errs:
            _append_log({"status": "warn", "betId": bet_id, "normalizeErrors": errs})

        container[idx] = normalized
        save_json(source_path, payload)

        settled += 1

    _append_log({"status": "ok", "settled": settled})
    return {"status": "ok", "settled": settled}
