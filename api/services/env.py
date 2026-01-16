import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
THESPORTSDB_KEY = os.getenv("THESPORTSDB_KEY")

if not API_FOOTBALL_KEY:
    raise RuntimeError("API_FOOTBALL_KEY no configurada")

if not THESPORTSDB_KEY:
    raise RuntimeError("THESPORTSDB_KEY no configurada")
