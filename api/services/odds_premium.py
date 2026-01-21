import json
from pathlib import Path
from datetime import date


PREMIUM_PROBABILITY_THRESHOLD = 0.86


def classify_premium(selection: dict) -> bool:
    risk = selection.get("risk")
    p_est = selection.get("p_est")

    if not risk or p_est is None:
        return False

    return (
        risk.get("level") == "LOW"
        and p_est >= PREMIUM_PROBABILITY_THRESHOLD
    )


def process_premium(input_path: Path, output_path: Path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for event in data:
        for market in event.get("markets", []):
            for selection in market.get("selections", []):
                selection["premium"] = classify_premium(selection)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_today():
    today = date.today().isoformat()

    input_path = Path(f"data/odds_risk/{today}/all.json")
    output_path = Path(f"data/odds_premium/{today}/all.json")

    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    process_premium(input_path, output_path)
    print(f"✅ Clasificación PREMIUM aplicada → {output_path}")


if __name__ == "__main__":
    run_today()
