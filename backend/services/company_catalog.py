import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Look in backend/data/ first, then fall back to the legacy src/backend/ location.
_CSV_CANDIDATES = [
    BASE_DIR / "data" / "EQUITY_L.csv",
    BASE_DIR.parent / "src" / "backend" / "EQUITY_L.csv",
]
CSV_FILE = next((p for p in _CSV_CANDIDATES if p.exists()), _CSV_CANDIDATES[0])
JSON_FILE = BASE_DIR / "data" / "companies.json"


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _catalog_is_fresh():
    return JSON_FILE.exists() and CSV_FILE.exists() and JSON_FILE.stat().st_mtime >= CSV_FILE.stat().st_mtime


def build_company_json():
    companies = []
    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            symbol = _clean(row.get("SYMBOL")).upper()
            name = _clean(row.get("NAME OF COMPANY"))
            if not symbol or not name:
                continue
            companies.append({
                "symbol": symbol,
                "nse_symbol": f"{symbol}.NS",
                "name": name,
                "display": f"{symbol} : {name}",
            })
    JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
    JSON_FILE.write_text(json.dumps(companies, ensure_ascii=False, indent=2), encoding="utf-8")
    return companies


def load_companies():
    if not CSV_FILE.exists():
        return []
    if not _catalog_is_fresh():
        return build_company_json()
    try:
        return json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return build_company_json()


def get_display_symbols():
    return [c["display"] for c in load_companies()]


def get_company_name_map():
    names = {}
    for c in load_companies():
        names[c["symbol"]] = c["name"]
        names[c["nse_symbol"]] = c["name"]
    return names


def normalize_nse_symbol(value):
    if not value:
        return ""
    raw = _clean(value).upper()
    companies = load_companies()
    symbols = {c["symbol"] for c in companies}
    display_map = {c["display"].upper(): c["symbol"] for c in companies}

    if raw in display_map:
        return f"{display_map[raw]}.NS"

    symbol = raw.split(":")[0].strip().split()[0].strip()
    if symbol.endswith(".NS"):
        symbol = symbol[:-3]
    symbol = "".join(ch for ch in symbol if ch.isalnum() or ch in {"-", "&"})
    if not symbol:
        return ""
    if symbol in symbols:
        return f"{symbol}.NS"

    # Not in CSV — try Yahoo Finance (catches new IPOs, demerged entities, renamed tickers)
    return _yf_verify(symbol)


def _yf_verify(symbol: str) -> str:
    """
    Confirm a symbol exists on NSE via Yahoo Finance search.
    Returns 'SYMBOL.NS' if found, empty string otherwise.
    Called only when the symbol is absent from the local CSV.
    """
    try:
        import requests
        resp = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": symbol, "quotesCount": 5, "newsCount": 0, "listsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        for quote in resp.json().get("quotes", []):
            sym = quote.get("symbol", "")
            if quote.get("quoteType") == "EQUITY" and sym.upper() == f"{symbol}.NS":
                return sym
    except Exception:
        pass
    return ""
