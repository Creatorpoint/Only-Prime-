import telebot
import json
import random
import openai
import threading
import schedule
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_ID, OPENAI_KEY, BOT_USERNAME

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_KEY

selected_groups = {}

# DATABASE

def load_db():
    with open("database.json") as f:
        return json.load(f)

def save_db(d):
    with open("database.json","w") as f:
        json.dump(d,f)

# START

@bot.message_handler(commands=['start'])
def start(m):

    db = load_db()
    uid = m.from_user.id

    if uid not in db["users"]:
        db["users"].append(uid)
        db["memory"][str(uid)] = []
        save_db(db)

    bot.send_message(m.chat.id,"🤖 AI Bot Activated")

# ADD GROUP

@bot.message_handler(commands=['addgroup'])
def add_group(m):

    if m.from_user.id != ADMIN_ID:
        return

    gid = int(m.text.split()[1])

    db = load_db()

    if gid not in db["groups"]:
        db["groups"].append(gid)
        save_db(db)

    bot.send_message(m.chat.id,"✅ Group Added")

# ADMIN ANALYTICS

@bot.message_handler(commands=['admin'])
def admin(m):

    if m.from_user.id != ADMIN_ID:
        return

    db = load_db()

    text = f"""
📊 BOT ANALYTICS

Users : {len(db['users'])}
Groups : {len(db['groups'])}
Blocked : {len(db['blocked'])}
"""

    bot.send_message(m.chat.id,text)

# GROUP SELECT BROADCAST

@bot.message_handler(commands=['broadcast'])
def broadcast(m):

    if m.from_user.id != ADMIN_ID:
        return

    db = load_db()

    k = InlineKeyboardMarkup()

    for g in db["groups"]:
        k.add(InlineKeyboardButton(f"Group {g}",callback_data=f"bc_{g}"))

    bot.send_message(m.chat.id,"👥 Select group",reply_markup=k)

# GROUP CLICK

@bot.callback_query_handler(func=lambda c:c.data.startswith("bc_"))
def select_group(c):

    gid = int(c.data.split("_")[1])

    selected_groups[c.from_user.id] = gid

    msg = bot.send_message(c.message.chat.id,"Send broadcast content")

    bot.register_next_step_handler(msg,send_selected)

# SEND BROADCAST

def send_selected(message):

    gid = selected_groups.get(message.from_user.id)

    if not gid:
        return

    try:

        if message.text:
            bot.send_message(gid,message.text)

        elif message.photo:
            bot.send_photo(gid,message.photo[-1].file_id,caption=message.caption)

        elif message.video:
            bot.send_video(gid,message.video.file_id,caption=message.caption)

        bot.send_message(message.chat.id,"✅ Broadcast sent")

    except:
        bot.send_message(message.chat.id,"❌ Failed")

# AI CHAT

@bot.message_handler(func=lambda m: True)
def ai_chat(message):

    if not message.text:
        return

    db = load_db()
    uid = str(message.from_user.id)

    if uid not in db["memory"]:
        db["memory"][uid] = []

    db["memory"][uid].append(message.text)

    save_db(db)

    trigger = BOT_USERNAME.lower() in message.text.lower() or "bot" in message.text.lower()

    if not trigger:
        return

    try:

        history = db["memory"][uid][-5:]

        msgs = [{"role":"system","content":"You are a funny helpful assistant"}]

        for h in history:
            msgs.append({"role":"user","content":h})

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=msgs
        )

        reply = response["choices"][0]["message"]["content"]

        bot.reply_to(message,reply)

    except:

        jokes = [
        "😂 Thinking...",
        "🤖 Brain loading",
        "🤣 Try again"
        ]

        bot.reply_to(message,random.choice(jokes))

# AUTO GROUP ENGAGEMENT

def auto_chat():

    db = load_db()

    msgs = [
    "👀 Anyone online?",
    "😂 Drop meme",
    "🔥 Who is active?",
    "🤖 Ask me anything"
    ]

    for g in db["groups"]:
        try:
            bot.send_message(g,random.choice(msgs))
        except:
            pass

schedule.every(25).minutes.do(auto_chat)

# SCHEDULER

def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler).start()

bot.infinity_polling()
