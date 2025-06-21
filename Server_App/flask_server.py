from flask import Flask ,request, render_template, session, redirect, url_for
import sqlite3
from hashlib import sha256
from contextlib import closing
from random import randint
import os

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
def hello_world():
   return 'Hello World'

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
                conn.execute('''
                    INSERT INTO users (username,email, password_hash)
                    VALUES (?, ?, ?)
                    ''', (user_name, user_email, user_password))
                user_id = conn.cursor().lastrowid
                conn.commit()

        session["user_id"] = user_id
        session["user_name"] = user_name
        return render_template("finscope.html")
    else:
        return 'bad request!', 400

@app.route("/login", methods = ['POST', 'GET'])
def login():
   if request.method == "GET":
        return render_template("login.html")
   elif request.method == "POST":
        email_entered    = request.form.get(email)
        password_entered = sha256(request.form.get(email).encode('utf-8')).hexdigest()
        
        with conn:
                conn.execute('''
                    INSERT INTO users (username,email, password_hash)
                    VALUES (?, ?, ?)
                    ''', (user_name, user_email, user_password))
                user_id = conn.cursor().lastrowid
                conn.commit()

        return render_template("finscope.html")
   else:
        return 'bad request!', 400

if __name__ == '__main__':
    app.run()



    