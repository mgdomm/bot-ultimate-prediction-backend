import sys
import os
import json
from datetime import datetime

# Añadir raíz del proyecto al PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from services.settlement_service import settle_all_pending_bets


def main():
    result = settle_all_pending_bets()
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "result": result
    }
    print(json.dumps(log_entry, ensure_ascii=False))


if __name__ == "__main__":
    main()
