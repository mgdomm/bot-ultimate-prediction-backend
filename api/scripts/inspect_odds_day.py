import json
import sys
from pathlib import Path

def summarize_json(obj):
    if isinstance(obj, list):
        return {"type": "list", "len": len(obj)}
    if isinstance(obj, dict):
        keys = list(obj.keys())
        out = {"type": "dict", "keys_n": len(keys), "keys_head": keys[:15]}
        # Heurísticas típicas
        for k in ["data", "results", "events", "odds", "response", "items", "matches", "games", "leagues"]:
            v = obj.get(k, None)
            if isinstance(v, list):
                out[f"list_key:{k}"] = len(v)
            elif isinstance(v, dict):
                out[f"dict_key:{k}"] = len(v.keys())
        return out
    return {"type": type(obj).__name__}

def safe_load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return e

def main(day: str):
    repo = Path(__file__).resolve().parents[2]
    odds_dir = repo / "api" / "data" / "odds" / day
    print(f"DAY={day}")
    print(f"ODDS_DIR={odds_dir}")
    if not odds_dir.exists():
        print("ERROR: odds_dir does not exist")
        sys.exit(2)

    files = sorted(odds_dir.glob("*.json"))
    print(f"FILES={len(files)}")

    nonempty_files = 0
    for p in files:
        size = p.stat().st_size
        obj = safe_load(p)
        if isinstance(obj, Exception):
            print(f"- {p.name}: size={size} JSON_ERROR={obj}")
            continue

        summary = summarize_json(obj)
        # “no vacío” real: no es [] y no es {}
        is_nonempty = not (obj == [] or obj == {})
        if is_nonempty:
            nonempty_files += 1

        print(f"- {p.name}: size={size} nonempty={is_nonempty} summary={summary}")

        # Muestra mínima (sin spamear)
        if isinstance(obj, dict):
            for k in ["data", "results", "events", "odds", "response"]:
                v = obj.get(k)
                if isinstance(v, list) and len(v) > 0:
                    head = v[0]
                    head_type = type(head).__name__
                    head_keys = list(head.keys())[:20] if isinstance(head, dict) else None
                    print(f"  sample[{k}][0]: type={head_type} keys_head={head_keys}")
                    break
        elif isinstance(obj, list) and len(obj) > 0:
            head = obj[0]
            head_type = type(head).__name__
            head_keys = list(head.keys())[:20] if isinstance(head, dict) else None
            print(f"  sample[0]: type={head_type} keys_head={head_keys}")

    print(f"NONEMPTY_FILES={nonempty_files}/{len(files)}")

if __name__ == "__main__":
    day = sys.argv[1] if len(sys.argv) > 1 else None
    if not day:
        print("USAGE: python3 -u api/scripts/inspect_odds_day.py YYYY-MM-DD")
        sys.exit(2)
    main(day)
