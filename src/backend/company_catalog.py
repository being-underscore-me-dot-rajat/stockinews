import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "EQUITY_L.csv"
JSON_FILE = BASE_DIR / "companies.json"


def _clean_text(value):
    return " ".join(str(value or "").strip().split())


def _catalog_is_fresh():
    return JSON_FILE.exists() and JSON_FILE.stat().st_mtime >= CSV_FILE.stat().st_mtime


def build_company_json():
    companies = []
    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            symbol = _clean_text(row.get("SYMBOL")).upper()
            name = _clean_text(row.get("NAME OF COMPANY"))
            if not symbol or not name:
                continue
            companies.append({
                "symbol": symbol,
                "nse_symbol": f"{symbol}.NS",
                "name": name,
                "display": f"{symbol} : {name}",
            })

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
    return [company["display"] for company in load_companies()]


def get_company_name_map():
    names = {}
    for company in load_companies():
        names[company["symbol"]] = company["name"]
        names[company["nse_symbol"]] = company["name"]
    return names


def normalize_nse_symbol(value):
    if not value:
        return ""

    raw = _clean_text(value).upper()
    symbols = {company["symbol"] for company in load_companies()}
    display_to_symbol = {
        company["display"].upper(): company["symbol"]
        for company in load_companies()
    }

    if raw in display_to_symbol:
        return f"{display_to_symbol[raw]}.NS"

    symbol = raw.split(":")[0].strip()
    symbol = symbol.split()[0].strip()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    symbol = "".join(char for char in symbol if char.isalnum() or char in {"-", "&"})
    if not symbol:
        return ""

    return f"{symbol}.NS" if symbol in symbols else ""
