from flask import Flask, request, jsonify
import sqlite3

DB_NAME = "src/backend/stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_user(decoded_token):
    user_id = decoded_token["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return {"name": row[0], "email": row[1]}
