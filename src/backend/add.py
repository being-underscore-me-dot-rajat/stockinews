from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from company_catalog import normalize_nse_symbol

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def add_watchlist(user_id):
    symbol = normalize_nse_symbol(request.json.get("symbol", ""))
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, symbol))
    if cur.fetchone():
        conn.close()
        return jsonify({"message": "Symbol already in watchlist"}), 200

    cur.execute("INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)", (user_id, symbol))
    conn.commit()
    conn.close()
    return jsonify({"message": "Added"}), 201
