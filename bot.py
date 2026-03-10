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
        db["memory"][str(uid)]=[]
        save_db(db)

    bot.send_message(m.chat.id,"👋 Hello I'm Smart AI Bot 🤖")

# ADMIN PANEL

@bot.message_handler(commands=['admin'])
def admin(m):

    if m.from_user.id!=ADMIN_ID:
        return

    k=InlineKeyboardMarkup()

    k.add(
    InlineKeyboardButton("📊 Analytics",callback_data="stats"),
    InlineKeyboardButton("📢 Broadcast",callback_data="bc")
    )

    k.add(
    InlineKeyboardButton("👥 Groups",callback_data="groups"),
    InlineKeyboardButton("🚫 Block",callback_data="block")
    )

    bot.send_message(m.chat.id,"👑 Admin Panel",reply_markup=k)

# ANALYTICS

@bot.callback_query_handler(func=lambda c:c.data=="stats")
def stats(c):

    db=load_db()

    text=f"""
📊 BOT ANALYTICS

👤 Users : {len(db['users'])}
👥 Groups : {len(db['groups'])}
🚫 Blocked : {len(db['blocked'])}
"""

    bot.edit_message_text(text,c.message.chat.id,c.message.message_id)

# BROADCAST ENGINE

@bot.message_handler(commands=['broadcast'])
def bc(m):

    if m.from_user.id!=ADMIN_ID:
        return

    msg=bot.send_message(m.chat.id,"Send message/photo/video")

    bot.register_next_step_handler(msg,process_bc)

def process_bc(message):

    db=load_db()
    sent=0

    targets=db["users"]+db["groups"]

    for t in targets:

        try:

            if message.text:
                bot.send_message(t,message.text)

            elif message.photo:
                bot.send_photo(t,message.photo[-1].file_id,caption=message.caption)

            elif message.video:
                bot.send_video(t,message.video.file_id,caption=message.caption)

            sent+=1

        except:
            pass

    bot.send_message(message.chat.id,f"✅ Broadcast Sent {sent}")

# BUTTON BROADCAST

def button_broadcast(text,btn,link):

    db=load_db()

    k=InlineKeyboardMarkup()
    k.add(InlineKeyboardButton(btn,url=link))

    for u in db["users"]:
        try:
            bot.send_message(u,text,reply_markup=k)
        except:
            pass

# ADD GROUP

@bot.message_handler(commands=['addgroup'])
def addg(m):

    if m.from_user.id!=ADMIN_ID:
        return

    gid=int(m.text.split()[1])

    db=load_db()

    if gid not in db["groups"]:
        db["groups"].append(gid)
        save_db(db)

    bot.send_message(m.chat.id,"✅ Group Added")

# FUNNY MEME REPLIES

memes=[
"😂 Bro that's illegal!",
"🤣 Developer life be like",
"💀 RIP logic",
"😂 That escalated quickly"
]

# AI CHAT + MEMORY

@bot.message_handler(func=lambda m:m.chat.type in ["group","supergroup"])
def ai_chat(m):

    if not m.text:
        return

    db=load_db()

    uid=str(m.from_user.id)

    if uid not in db["memory"]:
        db["memory"][uid]=[]

    db["memory"][uid].append(m.text)

    save_db(db)

    if BOT_USERNAME not in m.text and "bot" not in m.text.lower():
        if random.randint(1,20)==5:
            bot.reply_to(m,random.choice(memes))
        return

    try:

        history=db["memory"][uid][-5:]

        messages=[{"role":"system","content":"You are a funny helpful Telegram group assistant."}]

        for h in history:
            messages.append({"role":"user","content":h})

        response=openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages
        )

        reply=response["choices"][0]["message"]["content"]

        bot.reply_to(m,reply)

    except:
        bot.reply_to(m,"🤖 Thinking...")

# AUTO TALKING AI

def auto_chat():

    db=load_db()

    msgs=[
    "👀 Anyone online?",
    "😂 Drop your best meme",
    "🤖 Ask me anything!",
    "🔥 Who is active?"
    ]

    for g in db["groups"]:

        try:
            bot.send_message(g,random.choice(msgs))
        except:
            pass

schedule.every(30).minutes.do(auto_chat)

# SCHEDULE BROADCAST

def schedule_msg(text,time_set):

    db=load_db()

    def job():

        for g in db["groups"]:
            try:
                bot.send_message(g,text)
            except:
                pass

    schedule.every().day.at(time_set).do(job)

# SCHEDULER

def scheduler():

    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler).start()

bot.infinity_polling()
