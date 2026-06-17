from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from company_catalog import normalize_nse_symbol

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


def delete_watchlist(user_id, symbol):
    normalized_symbol = normalize_nse_symbol(symbol)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker IN (?, ?)", (user_id, symbol.upper(), normalized_symbol))
    conn.commit()
    conn.close()
    return jsonify({"message": "Removed"}), 200
