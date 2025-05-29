from flask import Flask, request, jsonify
import sqlite3
DB_NAME = "src/backend/stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


def delete_watchlist(user_id, symbol):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, symbol.upper()))
    conn.commit()
    conn.close()
    return jsonify({"message": "Removed"}), 200