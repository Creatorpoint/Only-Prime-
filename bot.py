import telebot
import json
import schedule
import time
import threading
from telebot.types import ReplyKeyboardMarkup
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

# DATABASE
def load_db():
    with open("database.json") as f:
        return json.load(f)

def save_db(data):
    with open("database.json","w") as f:
        json.dump(data,f)

# MENU
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📢 Broadcast","📊 Stats")
    m.row("👥 Groups","🚫 Block User")
    m.row("⏰ Schedule","❓ Help")
    return m

# START
@bot.message_handler(commands=['start'])
def start(msg):

    db = load_db()

    if msg.from_user.id not in db["users"]:
        db["users"].append(msg.from_user.id)
        save_db(db)

    bot.send_message(
        msg.chat.id,
        "👋 Welcome Professional Broadcast Bot 🚀",
        reply_markup=menu()
    )

# HELP
@bot.message_handler(func=lambda m: m.text=="❓ Help")
def help(msg):

    bot.send_message(msg.chat.id,
"""
🤖 BOT COMMANDS

/start
/addgroup
/broadcast
/stats
/block id
/unblock id
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
🚫 Blocked : {len(db['blocked'])}
""")

# ADD GROUP
@bot.message_handler(commands=['addgroup'])
def addgroup(msg):

    if msg.chat.type in ["group","supergroup"]:

        db = load_db()

        if msg.chat.id not in db["groups"]:
            db["groups"].append(msg.chat.id)
            save_db(db)

            bot.send_message(msg.chat.id,"✅ Group Linked")

# BROADCAST
@bot.message_handler(func=lambda m: m.text=="📢 Broadcast")
def ask_broadcast(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    bot.send_message(msg.chat.id,"Send message for broadcast")

    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(msg):

    db = load_db()

    success=0

    for u in db["users"]:
        try:
            bot.send_message(u,msg.text)
            success+=1
        except:
            pass

    for g in db["groups"]:
        try:
            bot.send_message(g,msg.text)
            success+=1
        except:
            pass

    bot.send_message(msg.chat.id,f"✅ Broadcast Done\nSent : {success}")

# BLOCK USER
@bot.message_handler(commands=['block'])
def block(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    uid=int(msg.text.split()[1])

    db=load_db()

    db["blocked"].append(uid)

    save_db(db)

    bot.send_message(msg.chat.id,"🚫 User Blocked")

# UNBLOCK
@bot.message_handler(commands=['unblock'])
def unblock(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    uid=int(msg.text.split()[1])

    db=load_db()

    db["blocked"].remove(uid)

    save_db(db)

    bot.send_message(msg.chat.id,"✅ User Unblocked")

# SCHEDULE
def scheduled_job(text):

    db = load_db()

    for u in db["users"]:
        try:
            bot.send_message(u,text)
        except:
            pass

@bot.message_handler(func=lambda m: m.text=="⏰ Schedule")
def schedule_msg(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    bot.send_message(msg.chat.id,"Send message to schedule")

    bot.register_next_step_handler(msg,set_schedule)

def set_schedule(msg):

    schedule.every(1).minutes.do(scheduled_job,msg.text)

    bot.send_message(msg.chat.id,"⏰ Message scheduled every 1 minute")

# SCHEDULER THREAD
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule).start()

bot.infinity_polling()
