import telebot
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

# DATABASE
def load_db():
    with open("database.json") as f:
        return json.load(f)

def save_db(data):
    with open("database.json","w") as f:
        json.dump(data,f)

# MENU BUTTONS
def menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Broadcast","📊 Stats")
    markup.row("👥 Groups","❓ Help")
    return markup

# START
@bot.message_handler(commands=['start'])
def start(msg):

    db = load_db()

    if msg.from_user.id not in db["users"]:
        db["users"].append(msg.from_user.id)
        save_db(db)

    bot.send_message(
        msg.chat.id,
        "👋 Welcome Broadcast Bot 🚀",
        reply_markup=menu()
    )

# HELP
@bot.message_handler(func=lambda m: m.text=="❓ Help")
def help(msg):

    bot.send_message(msg.chat.id,
"""
🤖 BOT COMMANDS

/start
/broadcast message
/addgroup
/stats
""")

# STATS
@bot.message_handler(func=lambda m: m.text=="📊 Stats")
def stats(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    db = load_db()

    bot.send_message(msg.chat.id,
f"""
📊 BOT STATS

👤 Users : {len(db['users'])}
👥 Groups : {len(db['groups'])}
""")

# ADD GROUP
@bot.message_handler(commands=['addgroup'])
def addgroup(msg):

    if msg.chat.type in ["group","supergroup"]:

        db = load_db()

        if msg.chat.id not in db["groups"]:
            db["groups"].append(msg.chat.id)
            save_db(db)

            bot.send_message(msg.chat.id,"✅ Group Added")

# BROADCAST BUTTON
@bot.message_handler(func=lambda m: m.text=="📢 Broadcast")
def ask_broadcast(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    bot.send_message(msg.chat.id,"Send message for broadcast")

    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(msg):

    db = load_db()

    success = 0

    for user in db["users"]:
        try:
            bot.send_message(user,msg.text)
            success+=1
        except:
            pass

    for group in db["groups"]:
        try:
            bot.send_message(group,msg.text)
            success+=1
        except:
            pass

    bot.send_message(msg.chat.id,f"✅ Broadcast Done\nSent : {success}")

bot.infinity_polling()
