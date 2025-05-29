import sqlite3
import bcrypt
import jwt
import datetime
import os
from flask import Flask, request, jsonify


DB_NAME = "src/backend/stockinews.db"
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")  # Change this in production!
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # Token valid for 1 hour

def get_connection():
    return sqlite3.connect(DB_NAME)

def login_user(email, password):
    conn = get_connection()
    # if conn:
    #     print("connection established")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"error": "Invalid email or password"}, 401

    user_id, name, email, hashed_pw = user

    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
        return {"error": "Invalid email or password"}, 401

    # Create JWT token
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }, 200

def signup(name,email,password):

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_pw))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400
    finally:
        conn.close()

    token = jwt.encode({
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({
        "message": "User registered successfully",
        "token": token
    }), 201
