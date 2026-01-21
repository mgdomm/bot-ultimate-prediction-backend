import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from api.services.settlement.resolvers.football import FootballResolver
from api.services.settlement.resolvers.tennis import TennisResolver


class SettlementBuilder:
    def __init__(self, api_client, data_path: Path):
        self.api_client = api_client
        self.data_path = data_path

        self.resolvers = {
            "football": FootballResolver(api_client),
            "tennis": TennisResolver(api_client),
        }

    def _contract_path(self, date: str) -> Path:
        return self.data_path / "contracts" / date / "contract.json"

    def _settlement_path(self, date: str) -> Path:
        return self.data_path / "settlements" / date / "settlement.json"

    def _hash_contract(self, contract: dict) -> str:
        raw = json.dumps(contract, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def _resolve_parlay(self, legs):
        results = [leg["result"] for leg in legs]

        if "LOSS" in results:
            return "LOSS"
        if all(r == "WIN" for r in results):
            return "WIN"
        if "VOID" in results and all(r in ("WIN", "VOID") for r in results):
            return "VOID"

        return "VOID"

    def build(self, date: str) -> None:
        contract_path = self._contract_path(date)
        settlement_path = self._settlement_path(date)

        if settlement_path.exists():
            return

        if not contract_path.exists():
            return

        with open(contract_path, "r") as f:
            contract = json.load(f)

        settlement_path.parent.mkdir(parents=True, exist_ok=True)

        picks_results = []
        pick_result_map = {}

        for pick in contract.get("picks", []):
            sport = pick["sport"]
            resolver = self.resolvers.get(sport)

            if not resolver:
                continue

            resolved = resolver.resolve_pick(pick)

            pick_entry = {
                "pick_id": pick["pick_id"],
                "sport": sport,
                "event_id": pick["event_id"],
                "market": pick["market"],
                "selection": pick["selection"],
                "odds": pick["odds"],
                "result": resolved["result"],
                "resolver": sport,
                "evidence": resolved["evidence"],
            }

            picks_results.append(pick_entry)
            pick_result_map[pick["pick_id"]] = resolved["result"]

        parlays_results = []

        for parlay in contract.get("parlays", []):
            legs = []
            for leg in parlay.get("legs", []):
                result = pick_result_map.get(leg["pick_id"], "VOID")
                legs.append({
                    "pick_id": leg["pick_id"],
                    "result": result
                })

            final_result = self._resolve_parlay(legs)

            parlays_results.append({
                "parlay_id": parlay["parlay_id"],
                "legs": legs,
                "final_result": final_result
            })

        settlement = {
            "date": date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "api-sports",
            "picks": picks_results,
            "parlays": parlays_results,
            "integrity": {
                "contract_hash": self._hash_contract(contract),
                "deterministic": True,
            },
        }

        with open(settlement_path, "w") as f:
            json.dump(settlement, f, indent=2)
