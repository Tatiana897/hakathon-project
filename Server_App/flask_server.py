from flask import Flask ,request, render_template, session, redirect, url_for
import sqlite3
from hashlib import sha256
from contextlib import closing
from random import randint
import os
import GetTable
import pandas as pd

# Подключение к базе данных SQLite для хранения пользователей
conn = sqlite3.connect('bot_users.db')
cursor = conn.cursor()

# Создаем таблицу пользователей с добавленным столбцом для хранения языка
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL, 
        dataset_link TEXT DEFAULT NULL,
        language TEXT DEFAULT 'ru'
    );
''')


conn.commit()


app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def main():
   return render_template("main.html")

@app.route("/signup", methods = ['POST', 'GET'])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        user_name = request.form.get("name")
        user_email = request.form.get("email")
        user_password = request.form.get("password")
        user_password = sha256(user_password.encode('utf-8')).hexdigest()

        with closing(sqlite3.connect('bot_users.db')) as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username,email, password_hash)
                    VALUES (?, ?, ?)
                    ''', (user_name, user_email, user_password))
                user_id = cursor.lastrowid
                conn.commit()

        session["user_id"] = user_id
        session["user_name"] = user_name
        return redirect("company-info")
    else:
        return 'bad request!', 400

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    elif request.method == "POST":
        email_entered = request.form.get("email")
        password_entered = sha256(request.form.get("password").encode('utf-8')).hexdigest()
        
        with closing(sqlite3.connect('bot_users.db')) as conn:
            with conn:
                cursor = conn.cursor()
                
                # Ищем пользователя по email
                cursor.execute('''
                    SELECT user_id, password_hash FROM users 
                    WHERE email = ?
                ''', (email_entered,))
                
                user_data = cursor.fetchone()
                
                if user_data:
                    user_id, stored_password = user_data
                    
                    # Проверяем пароль
                    if password_entered == stored_password:
                        session['user_id'] = user_id  # Сохраняем в сессии
                        return redirect("/company-info")  # Перенаправляем после успешного входа
                    else:
                        return "Неверный пароль", 401
                else:
                    return "Пользователь с таким email не найден", 404
    else:
        return 'Bad Request', 400

@app.route("/company-info")
def company_info():
    try:
        user_id = session["user_id"]            
    except:
        return redirect("/login")

    with closing(sqlite3.connect('bot_users.db')) as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute('''
                                SELECT * FROM users 
                                WHERE user_id = ?
                            ''', (user_id,))
                            
                user_data = cursor.fetchone()

    username     = user_data[1]
    email        = user_data[2]
    dataset_link = user_data[4]

    if os.path.exists(username+".xlsx"):
        company_data = pd.read_excel(username + ".xlsx")
    else:
        company_data = GetTable.export_gsheet_to_excel("1-pI8FLZ1hBfAiKSc7NM847Hw9SyrRLG75FIcXIxYK9Q", username+".xlsx")

    return render_template("finscope.html", profile_name = username, profile_email = email)

if __name__ == '__main__':
    app.run()



    