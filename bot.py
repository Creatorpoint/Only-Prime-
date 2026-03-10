import telebot
import json
import random
import schedule
import time
import threading
import openai
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton
from config import TOKEN,ADMIN_ID,OPENAI_KEY,BOT_USERNAME

bot=telebot.TeleBot(TOKEN)
openai.api_key=OPENAI_KEY

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

    db=load_db()
    uid=m.from_user.id

    if uid not in db["users"]:
        db["users"].append(uid)
        db["balance"][str(uid)]=0
        save_db(db)

    bot.send_message(m.chat.id,"👋 Welcome to AI Pro Bot 🤖")

# ADMIN PANEL
@bot.message_handler(commands=['admin'])
def admin(m):

    if m.from_user.id!=ADMIN_ID:
        return

    k=InlineKeyboardMarkup()

    k.add(
    InlineKeyboardButton("📊 Dashboard",callback_data="dash"),
    InlineKeyboardButton("📢 Broadcast",callback_data="bc")
    )

    k.add(
    InlineKeyboardButton("👥 Groups",callback_data="groups"),
    InlineKeyboardButton("🚫 Block",callback_data="block")
    )

    k.add(
    InlineKeyboardButton("💰 Join Earn",callback_data="earn"),
    InlineKeyboardButton("⏰ Schedule",callback_data="schedule")
    )

    bot.send_message(m.chat.id,"👑 Admin Panel",reply_markup=k)

# DASHBOARD
@bot.callback_query_handler(func=lambda call:call.data=="dash")
def dash(call):

    db=load_db()

    bot.edit_message_text(
    f"""📊 DASHBOARD

👤 Users : {len(db['users'])}
👥 Groups : {len(db['groups'])}
🚫 Blocked : {len(db['blocked'])}
""",
    call.message.chat.id,
    call.message.message_id
    )

# BROADCAST
@bot.message_handler(commands=['broadcast'])
def broadcast(m):

    if m.from_user.id!=ADMIN_ID:
        return

    bot.send_message(m.chat.id,"Send broadcast message")

    bot.register_next_step_handler(m,send_bc)

def send_bc(m):

    db=load_db()

    sent=0

    for u in db["users"]:

        if u in db["blocked"]:
            continue

        try:
            bot.send_message(u,m.text)
            sent+=1
        except:
            pass

    for g in db["groups"]:
        try:
            bot.send_message(g,m.text)
            sent+=1
        except:
            pass

    bot.send_message(m.chat.id,f"✅ Broadcast sent: {sent}")

# ADD GROUP
@bot.message_handler(commands=['addgroup'])
def addgroup(m):

    if m.from_user.id!=ADMIN_ID:
        return

    gid=int(m.text.split()[1])

    db=load_db()

    if gid not in db["groups"]:
        db["groups"].append(gid)
        save_db(db)

    bot.send_message(m.chat.id,"✅ Group added")

# BLOCK
@bot.message_handler(commands=['block'])
def block(m):

    if m.from_user.id!=ADMIN_ID:
        return

    uid=int(m.text.split()[1])

    db=load_db()

    if uid not in db["blocked"]:
        db["blocked"].append(uid)
        save_db(db)

    bot.send_message(m.chat.id,"🚫 User blocked")

# JOIN TO EARN
@bot.message_handler(commands=['balance'])
def balance(m):

    db=load_db()

    uid=str(m.from_user.id)

    bal=db["balance"].get(uid,0)

    bot.send_message(m.chat.id,f"💰 Balance : {bal}")

# SCHEDULE BROADCAST
schedule_text=None

@bot.message_handler(commands=['schedule'])
def schedule_cmd(m):

    if m.from_user.id!=ADMIN_ID:
        return

    bot.send_message(m.chat.id,"Send time HH:MM")

    bot.register_next_step_handler(m,set_time)

def set_time(m):

    global sched_time
    sched_time=m.text

    bot.send_message(m.chat.id,"Send message")

    bot.register_next_step_handler(m,set_msg)

def set_msg(m):

    global schedule_text
    schedule_text=m.text

    schedule.every().day.at(sched_time).do(run_schedule)

    bot.send_message(m.chat.id,"⏰ Scheduled broadcast set")

def run_schedule():

    db=load_db()

    for u in db["users"]:
        try:
            bot.send_message(u,schedule_text)
        except:
            pass

# AI CHAT
@bot.message_handler(func=lambda m:m.chat.type in ["group","supergroup"])
def ai_chat(m):

    if not m.text:
        return

    if BOT_USERNAME not in m.text and "bot" not in m.text.lower():
        return

    try:

        response=openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
        {"role":"system","content":"You are a funny helpful Telegram group assistant who answers questions like a human."},
        {"role":"user","content":m.text}
        ]
        )

        reply=response["choices"][0]["message"]["content"]

        bot.reply_to(m,reply)

    except:
        bot.reply_to(m,"😅 AI busy right now")

# SCHEDULER THREAD
def scheduler():

    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler).start()

bot.infinity_polling()
