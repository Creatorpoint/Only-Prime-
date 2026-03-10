import telebot
import json
import threading
from flask import Flask
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def load_db():
    with open("database.json") as f:
        return json.load(f)

def save_db(data):
    with open("database.json","w") as f:
        json.dump(data,f)

@bot.message_handler(commands=['start'])
def start(msg):

    db = load_db()

    if msg.from_user.id not in db["users"]:
        db["users"].append(msg.from_user.id)
        save_db(db)

    bot.send_message(msg.chat.id,"👋 Welcome Broadcast Bot 🚀")

@bot.message_handler(commands=['addgroup'])
def addgroup(msg):

    if msg.chat.type in ["group","supergroup"]:

        db = load_db()

        if msg.chat.id not in db["groups"]:
            db["groups"].append(msg.chat.id)
            save_db(db)

            bot.send_message(msg.chat.id,"✅ Group Added")

@bot.message_handler(commands=['stats'])
def stats(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    db = load_db()

    bot.send_message(msg.chat.id,
f"""
📊 BOT STATS

👤 Users : {len(db['users'])}
👥 Groups : {len(db['groups'])}
📡 Channels : {len(db['channels'])}
""")

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    text = msg.text.replace("/broadcast ","")

    db = load_db()

    for u in db["users"]:
        try:
            bot.send_message(u,text)
        except:
            pass

    for g in db["groups"]:
        try:
            bot.send_message(g,text)
        except:
            pass

    bot.send_message(msg.chat.id,"✅ Broadcast Sent")

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
