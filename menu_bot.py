import os
import pytz
from datetime import datetime, time
from telegram.ext import Updater, CommandHandler
from threading import Thread
import time as time_module

# Get token from environment variable (set this in Render)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
IST = pytz.timezone("Asia/Kolkata")

# ---------- SIMPLE WEEKLY MENU (EDIT ITEMS AS YOU LIKE) ----------
MENU = {
    0: {"breakfast": "Idli + Sambar",        "lunch": "Rajma Chawal",        "dinner": "Paneer + Roti"},
    1: {"breakfast": "Poha + Jalebi",        "lunch": "Chole Bhature",       "dinner": "Egg Curry + Rice"},
    2: {"breakfast": "Aloo Paratha + Curd",  "lunch": "Curd Rice",           "dinner": "Veg Pulao"},
    3: {"breakfast": "Upma",                 "lunch": "Dal + Rice",          "dinner": "Chicken Curry"},
    4: {"breakfast": "Masala Dosa",          "lunch": "Veg Biryani",         "dinner": "Kadhi + Rice"},
    5: {"breakfast": "Bread Omelette",       "lunch": "Pav Bhaji",           "dinner": "Fried Rice + Manchurian"},
    6: {"breakfast": "Chole Kulche",         "lunch": "Special Thali",       "dinner": "Veg Pulao + Papad"},
}

# Store all users who send /start
subscribers = set()


# ---------- HELPER FUNCTIONS ----------

def get_today_weekday():
    now_ist = datetime.now(IST)
    return now_ist.weekday()


def format_full_day_menu(weekday):
    m = MENU[weekday]
    day_name = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][weekday]
    return (
        f"📅 {day_name} Menu\n\n"
        f"🥣 Breakfast: {m['breakfast']}\n"
        f"🍛 Lunch: {m['lunch']}\n"
        f"🍽 Dinner: {m['dinner']}"
    )


# ---------- COMMAND HANDLERS ----------

def start(update, context):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)

    update.message.reply_text(
        "👋 Hi! Mess Menu Bot here.\n\n"
        "I will send you meal reminders.\n\n"
        "Commands:\n"
        "/today - Today's full menu\n"
        "/tomorrow - Tomorrow's menu\n"
        "/breakfast - Today's breakfast\n"
        "/lunch - Today's lunch\n"
        "/dinner - Tonight's dinner"
    )


def today(update, context):
    weekday = get_today_weekday()
    update.message.reply_text(format_full_day_menu(weekday))


def tomorrow(update, context):
    weekday = (get_today_weekday() + 1) % 7
    update.message.reply_text(format_full_day_menu(weekday))


def breakfast(update, context):
    weekday = get_today_weekday()
    m = MENU[weekday]
    update.message.reply_text(f"🥣 Today's Breakfast: {m['breakfast']}")


def lunch(update, context):
    weekday = get_today_weekday()
    m = MENU[weekday]
    update.message.reply_text(f"🍛 Today's Lunch: {m['lunch']}")


def dinner(update, context):
    weekday = get_today_weekday()
    m = MENU[weekday]
    update.message.reply_text(f"🍽 Tonight's Dinner: {m['dinner']}")


# ---------- SCHEDULER THREAD FOR REMINDERS ----------

def reminder_loop(updater):
    """Runs in a separate thread to send reminders at fixed times."""
    while True:
        now = datetime.now(IST)
        current_time = now.time()

        # Define reminder times (24h format, IST)
        breakfast_time = time(8, 0)
        lunch_time = time(13, 0)
        dinner_time = time(20, 0)

        weekday = now.weekday()
        m = MENU[weekday]

        # Breakfast reminder
        if current_time.hour == breakfast_time.hour and current_time.minute == breakfast_time.minute:
            text = f"⏰ Breakfast Reminder!\n\n🥣 {m['breakfast']}"
            for chat_id in list(subscribers):
                updater.bot.send_message(chat_id=chat_id, text=text)
            time_module.sleep(60)

        # Lunch reminder
        if current_time.hour == lunch_time.hour and current_time.minute == lunch_time.minute:
            text = f"⏰ Lunch Reminder!\n\n🍛 {m['lunch']}"
            for chat_id in list(subscribers):
                updater.bot.send_message(chat_id=chat_id, text=text)
            time_module.sleep(60)

        # Dinner reminder
        if current_time.hour == dinner_time.hour and current_time.minute == dinner_time.minute:
            text = f"⏰ Dinner Reminder!\n\n🍽 {m['dinner']}"
            for chat_id in list(subscribers):
                updater.bot.send_message(chat_id=chat_id, text=text)
            time_module.sleep(60)

        time_module.sleep(20)  # check every 20 seconds


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables!")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("today", today))
    dp.add_handler(CommandHandler("tomorrow", tomorrow))
    dp.add_handler(CommandHandler("breakfast", breakfast))
    dp.add_handler(CommandHandler("lunch", lunch))
    dp.add_handler(CommandHandler("dinner", dinner))

    # Start reminder thread
    t = Thread(target=reminder_loop, args=(updater,), daemon=True)
    t.start()

    # Start polling (keep bot running)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
