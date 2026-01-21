import json
from pathlib import Path
from datetime import date

STAKE_DEFAULT = 50.0


def classify_risk(selection: dict) -> dict:
    odds = selection.get("odds")
    p_est = selection.get("p_estimated")
    p_impl = selection.get("p_implied")
    ev = selection.get("ev")

    if odds is None or p_est is None or p_impl is None or ev is None:
        return None

    delta_p = p_est - p_impl
    ev_margin = ev / STAKE_DEFAULT

    # EXTREME — prioridad absoluta
    if (
        p_est < 0.50
        or ev_margin < 0.02
        or odds > 5.00
    ):
        level = "EXTREME"

    # LOW — ultra seguro
    elif (
        p_est >= 0.78
        and odds <= 1.65
        and ev_margin >= 0.02
        and abs(delta_p) <= 0.04
    ):
        level = "LOW"

    # MEDIUM — seguro controlado
    elif (
        p_est >= 0.65
        and odds <= 2.20
        and ev_margin >= 0.025
    ):
        level = "MEDIUM"

    # HIGH — valor con varianza
    else:
        level = "HIGH"

    return {
        "level": level,
        "p_est": round(p_est, 4),
        "delta_p": round(delta_p, 4),
        "ev_margin": round(ev_margin, 4),
    }


def run_today():
    today = date.today().isoformat()

    input_path = Path(f"data/odds_ev/{today}/all.json")
    output_path = Path(f"data/odds_risk/{today}/all.json")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for selection in data:
        risk = classify_risk(selection)
        if risk:
            selection["risk"] = risk

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Riesgo recalculado correctamente → {output_path}")


if __name__ == "__main__":
    run_today()
