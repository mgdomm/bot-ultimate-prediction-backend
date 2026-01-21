import json
from pathlib import Path
from collections import defaultdict


class StatsService:
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def _contract_path(self, date: str) -> Path:
        return self.data_path / "contracts" / date / "contract.json"

    def _settlement_path(self, date: str) -> Path:
        return self.data_path / "settlements" / date / "settlement.json"

    def _stats_path(self, date: str) -> Path:
        return self.data_path / "stats" / date / "stats.json"

    def _history_path(self) -> Path:
        return self.data_path / "stats" / "history.json"

    def _profit(self, stake: float, odds: float, result: str) -> float:
        if result == "WIN":
            return stake * (odds - 1)
        if result == "LOSS":
            return -stake
        return 0.0

    def build(self, date: str) -> None:
        contract_path = self._contract_path(date)
        settlement_path = self._settlement_path(date)
        stats_path = self._stats_path(date)

        if stats_path.exists():
            return

        if not contract_path.exists() or not settlement_path.exists():
            return

        with open(contract_path, "r") as f:
            contract = json.load(f)

        with open(settlement_path, "r") as f:
            settlement = json.load(f)

        stats_path.parent.mkdir(parents=True, exist_ok=True)

        tier_data = defaultdict(lambda: {
            "stake": 0.0,
            "profit": 0.0,
            "picks": 0
        })

        # PICKS
        pick_map = {p["pick_id"]: p for p in contract.get("picks", [])}

        for pick in settlement.get("picks", []):
            cp = pick_map.get(pick["pick_id"])
            if not cp:
                continue

            tier = cp.get("tier", "classic")
            stake = cp.get("stake", 0.0)
            profit = self._profit(stake, pick["odds"], pick["result"])

            tier_data[tier]["stake"] += stake
            tier_data[tier]["profit"] += profit
            tier_data[tier]["picks"] += 1

        # PARLAYS
        parlay_map = {p["parlay_id"]: p for p in contract.get("parlays", [])}

        for parlay in settlement.get("parlays", []):
            cp = parlay_map.get(parlay["parlay_id"])
            if not cp:
                continue

            tier = cp.get("tier", "classic")
            stake = cp.get("stake", 0.0)

            if parlay["final_result"] == "WIN":
                odds = 1.0
                for leg in parlay["legs"]:
                    pick = next(
                        p for p in settlement["picks"]
                        if p["pick_id"] == leg["pick_id"]
                    )
                    odds *= pick["odds"]
                profit = stake * (odds - 1)
            elif parlay["final_result"] == "LOSS":
                profit = -stake
            else:
                profit = 0.0

            tier_data[tier]["stake"] += stake
            tier_data[tier]["profit"] += profit

        tiers = {}
        for tier, d in tier_data.items():
            stake = d["stake"]
            profit = d["profit"]
            picks = d["picks"]

            roi = profit / stake if stake > 0 else 0.0
            yield_value = profit / picks if picks > 0 else 0.0

            tiers[tier] = {
                "stake": round(stake, 2),
                "profit": round(profit, 2),
                "roi": round(roi, 4),
                "yield": round(yield_value, 4),
                "picks": picks
            }

        daily_stats = {
            "date": date,
            "tiers": tiers
        }

        # GUARDAR STATS DIARIOS
        with open(stats_path, "w") as f:
            json.dump(daily_stats, f, indent=2)

        # HISTÓRICO
        history_path = self._history_path()
        history_path.parent.mkdir(parents=True, exist_ok=True)

        if history_path.exists():
            with open(history_path, "r") as f:
                history = json.load(f)
        else:
            history = {"history": []}

        if not any(e["date"] == date for e in history["history"]):
            history["history"].append(daily_stats)
            history["history"].sort(key=lambda x: x["date"])

            with open(history_path, "w") as f:
                json.dump(history, f, indent=2)
