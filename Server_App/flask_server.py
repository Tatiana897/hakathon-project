from flask import Flask ,request, render_template
import sqlite3

# Подключение к базе данных SQLite для хранения пользователей
conn = sqlite3.connect('bot_users.db')
cursor = conn.cursor()

# Создаем таблицу пользователей с добавленным столбцом для хранения языка
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL, 
        dataset_link TEXT,
        language TEXT DEFAULT 'ru'
    );
''')
conn.commit()
app = Flask(__name__)

@app.route('/')
def hello_world():
   return 'Hello World'

@app.route("/registration", methods = ['POST', 'GET'])
def registration():
	if request.method == "GET":
		return render_template("registration.html")
	elif request.method == "POST":
		pass
	else:
		return 'bad request!', 400

@app.route("/login", methods = ['POST', 'GET'])
def login():
   if request.method == "GET":
      return render_template("login.html")
   elif request.method == "POST":
      result = request.form.items()
      for key,value in result:
         print(key,value)
      return render_template("login.html")
   else:
      return 'bad request!', 400

if __name__ == '__main__':
   app.run()