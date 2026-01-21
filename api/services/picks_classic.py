import json
from pathlib import Path
from datetime import date

MAX_PICKS = 10
ALLOWED_RISKS = {"LOW", "MEDIUM"}


def generate_classic_picks(selections: list) -> list:
    candidates = []

    for sel in selections:
        ev = sel.get("ev")
        risk_level = sel.get("risk", {}).get("level")

        if ev is None or risk_level is None:
            continue

        if ev > 0 and risk_level in ALLOWED_RISKS:
            candidates.append(sel)

    # Ordenar por EV descendente
    candidates.sort(key=lambda x: x.get("ev", 0), reverse=True)

    return candidates[:MAX_PICKS]


def run_today():
    today = date.today().isoformat()

    input_path = Path(f"data/odds_premium/{today}/all.json")
    output_path = Path(f"data/picks_classic/{today}/all.json")

    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        selections = json.load(f)

    picks = generate_classic_picks(selections)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)

    print(f"✅ Picks clásicos generados: {len(picks)} → {output_path}")


if __name__ == "__main__":
    run_today()
