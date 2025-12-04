import os
import pytz
from datetime import datetime, timedelta, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in Render Environment Variables
IST = pytz.timezone("Asia/Kolkata")

# ===== Weekly Menu (Edit this) =====
MENU = {
    0: {"breakfast":"Idli + Sambar","lunch":"Rajma Chawal","dinner":"Paneer + Roti"},
    1: {"breakfast":"Poha + Jalebi","lunch":"Chole Bhature","dinner":"Egg Curry + Rice"},
    2: {"breakfast":"Aloo Paratha","lunch":"Curd Rice","dinner":"Veg Pulao"},
    3: {"breakfast":"Upma","lunch":"Dal + Rice","dinner":"Chicken Curry"},
    4: {"breakfast":"Dosa","lunch":"Biryani","dinner":"Kadhi + Rice"},
    5: {"breakfast":"Bread Omelette","lunch":"Pav Bhaji","dinner":"Fried Rice + Manchurian"},
    6: {"breakfast":"Chole Kulche","lunch":"Special Thali","dinner":"Veg Pulao + Papad"},
}

subscribers = set()   # multiple users supported


# ========== Commands ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)

    await update.message.reply_text(
        "🍽 Mess Menu Bot Activated!\n"
        "Commands:\n"
        "• /today\n• /tomorrow\n• /breakfast\n• /lunch\n• /dinner"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = datetime.now(IST).weekday()
    m = MENU[weekday]
    await update.message.reply_text(
        f"📅 TODAY MENU\n🥣 Breakfast: {m['breakfast']}\n🍛 Lunch: {m['lunch']}\n🍽 Dinner: {m['dinner']}"
    )


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = (datetime.now(IST).weekday()+1)%7
    m = MENU[weekday]
    await update.message.reply_text(
        f"📅 TOMORROW MENU\n🥣 Breakfast: {m['breakfast']}\n🍛 Lunch: {m['lunch']}\n🍽 Dinner: {m['dinner']}"
    )


async def breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = datetime.now(IST).weekday()
    await update.message.reply_text(f"🥣 Today's Breakfast: {MENU[weekday]['breakfast']}")


async def lunch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = datetime.now(IST).weekday()
    await update.message.reply_text(f"🍛 Today's Lunch: {MENU[weekday]['lunch']}")


async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = datetime.now(IST).weekday()
    await update.message.reply_text(f"🍽 Tonight's Dinner: {MENU[weekday]['dinner']}")


# ========== Scheduler Sends Daily Meals ==========

async def send_meal(context: ContextTypes.DEFAULT_TYPE):
    meal = context.job.data["meal"]
    weekday = datetime.now(IST).weekday()

    for user in subscribers:
        await context.bot.send_message(chat_id=user, text=f"🍽 {meal.upper()} REMINDER\n➡ {MENU[weekday][meal]}")


def main():
    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("breakfast", breakfast))
    app.add_handler(CommandHandler("lunch", lunch))
    app.add_handler(CommandHandler("dinner", dinner))

    # ⏰ Daily Timers (IST)
    app.job_queue.run_daily(send_meal, time=time(8,0, tzinfo=IST), data={"meal":"breakfast"})
    app.job_queue.run_daily(send_meal, time=time(13,0,tzinfo=IST), data={"meal":"lunch"})
    app.job_queue.run_daily(send_meal, time=time(20,0,tzinfo=IST), data={"meal":"dinner"})

    app.run_polling()


if __name__ == "__main__":
    main()

