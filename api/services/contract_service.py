from typing import Dict, List, Optional
from datetime import date, datetime
import json
from pathlib import Path

# Import robusto: funciona si ejecutas desde repo root o desde /api
try:
    from services.display_enrichment import enrich_contract_inplace
except ModuleNotFoundError:  # ejecución desde repo root
    from api.services.display_enrichment import enrich_contract_inplace  # type: ignore

CONTRACT_VERSION = "1.0"

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def create_empty_contract(contract_date: Optional[str] = None) -> Dict:
    if contract_date is None:
        contract_date = date.today().isoformat()

    return {
        "contract_version": CONTRACT_VERSION,
        "contract_date": contract_date,
        "generated_at": None,
        "picks_classic": [],
        "picks_parlay_premium": [],
        "daily_featured_parlay": None,
        "metadata": {},
    }


def _load_jsons_from_folder(folder: Path) -> List[Dict]:
    if not folder.exists():
        return []
    items: List[Dict] = []
    for p in sorted(folder.glob("*.json")):
        # Excluir agregadores internos del pipeline (no son picks individuales)
        if p.name in {"parlays.json"}:
            continue
        items.append(json.load(open(p, encoding="utf-8")))
    return items


def populate_contract_with_day_data(contract: Dict) -> Dict:
    day = contract["contract_date"]

    # picks_classic: preferimos el agregador all.json (lista plana de picks)
    classic_all = API_DATA_DIR / "picks_classic" / day / "all.json"
    if classic_all.exists():
        contract["picks_classic"] = json.load(open(classic_all, encoding="utf-8"))
    else:
        contract["picks_classic"] = _load_jsons_from_folder(
            API_DATA_DIR / "picks_classic" / day
        )

    contract["picks_parlay_premium"] = _load_jsons_from_folder(
        API_DATA_DIR / "picks_parlay" / day
    )

    featured_path = API_DATA_DIR / "picks_parlay_featured" / day / "featured_parlay.json"
    if featured_path.exists():
        contract["daily_featured_parlay"] = json.load(open(featured_path, encoding="utf-8"))


    # picks_value: sección opcional (value/inflated singles)
    value_all = API_DATA_DIR / "picks_value" / day / "all.json"
    if value_all.exists():
        contract["picks_value"] = json.load(open(value_all, encoding="utf-8"))
    else:
        contract["picks_value"] = []

    return contract


def freeze_and_save_contract(contract: Dict) -> Dict:
    # ✅ Enriquecimiento determinista con snapshots locales (nombres/logos)
    enrich_contract_inplace(contract)

    contract["generated_at"] = datetime.utcnow().isoformat()

    day = contract["contract_date"]
    base_path = API_DATA_DIR / "contracts" / day
    base_path.mkdir(parents=True, exist_ok=True)

    file_path = base_path / "contract.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    return contract
