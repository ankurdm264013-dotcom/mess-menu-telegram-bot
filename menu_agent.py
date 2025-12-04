import logging
from datetime import datetime, time, timedelta
import pytz

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ========= CONFIG =========
TELEGRAM_BOT_TOKEN = "8535766756:AAFjSXvBBZrtKC5olBvtLKZ89yDsI_yFzeY"
IST = pytz.timezone("Asia/Kolkata")

# ======== SIMPLE WEEKLY MENU (EDIT THIS FOR YOUR HOSTEL) =========
# weekday: Monday=0 ... Sunday=6
MENU = [
    # MONDAY
    {"weekday": 0, "meal_type": "breakfast", "items": "Idli, Sambar, Coconut Chutney, Tea"},
    {"weekday": 0, "meal_type": "lunch",     "items": "Rajma, Rice, Roti, Salad, Buttermilk"},
    {"weekday": 0, "meal_type": "dinner",    "items": "Paneer Butter Masala, Naan, Jeera Rice, Gulab Jamun"},

    # TUESDAY
    {"weekday": 1, "meal_type": "breakfast", "items": "Poha, Jalebi, Tea"},
    {"weekday": 1, "meal_type": "lunch",     "items": "Chole, Bhature, Rice, Salad"},
    {"weekday": 1, "meal_type": "dinner",    "items": "Egg Curry, Rice, Chapati, Kheer"},

    # WEDNESDAY
    {"weekday": 2, "meal_type": "breakfast", "items": "Aloo Paratha, Curd, Pickle"},
    {"weekday": 2, "meal_type": "lunch",     "items": "Sambar Rice, Poriyal, Curd, Papad"},
    {"weekday": 2, "meal_type": "dinner",    "items": "Veg Pulao, Raita, Chips"},

    # THURSDAY
    {"weekday": 3, "meal_type": "breakfast", "items": "Upma, Chutney, Tea"},
    {"weekday": 3, "meal_type": "lunch",     "items": "Dal Fry, Jeera Rice, Chapati, Salad"},
    {"weekday": 3, "meal_type": "dinner",    "items": "Chicken Curry, Rice, Chapati (or Paneer for veg)"},
    
    # FRIDAY
    {"weekday": 4, "meal_type": "breakfast", "items": "Masala Dosa, Sambar, Chutney"},
    {"weekday": 4, "meal_type": "lunch",     "items": "Veg Biryani, Raita, Salad"},
    {"weekday": 4, "meal_type": "dinner",    "items": "Kadhi, Rice, Aloo Sabzi, Chapati"},

    # SATURDAY
    {"weekday": 5, "meal_type": "breakfast", "items": "Bread, Butter, Jam, Boiled Egg"},
    {"weekday": 5, "meal_type": "lunch",     "items": "Pav Bhaji, Salad"},
    {"weekday": 5, "meal_type": "dinner",    "items": "Fried Rice, Manchurian, Ice Cream"},

    # SUNDAY
    {"weekday": 6, "meal_type": "breakfast", "items": "Chole Bhature, Lassi"},
    {"weekday": 6, "meal_type": "lunch",     "items": "Special Thali (Dal, Sabzi, Rice, Roti, Sweet)"},
    {"weekday": 6, "meal_type": "dinner",    "items": "Pulao, Raita, Papad"},
]

MEAL_LABELS = {
    "breakfast": "🥣 Breakfast",
    "lunch": "🍛 Lunch",
    "dinner": "🍽 Dinner",
}

# ========= LOGGING =========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========= HELPER FUNCTIONS =========

def get_today_weekday():
    """Return weekday number in IST (0=Mon ... 6=Sun)."""
    now_ist = datetime.now(IST)
    return now_ist.weekday(), now_ist.date()


def get_menu_for(weekday: int, meal_type: str | None = None):
    """Fetch menu entries for a given weekday, optionally filtered by meal_type."""
    results = []
    for row in MENU:
        if row["weekday"] == weekday:
            if meal_type is None or row["meal_type"] == meal_type:
                results.append(row)
    return results


def format_menu_message(weekday: int, date_obj, meal_type: str | None = None) -> str:
    day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
    date_str = date_obj.strftime("%d %b %Y")

    if meal_type:
        entries = get_menu_for(weekday, meal_type)
        if not entries:
            return f"No {meal_type} menu found for {day_name}, {date_str}."
        row = entries[0]
        header = MEAL_LABELS.get(meal_type, meal_type.capitalize())
        return f"{header} - {day_name}, {date_str}\n\nItems:\n• " + "\n• ".join(
            [item.strip() for item in row["items"].split(",")]
        )
    else:
        entries = get_menu_for(weekday, None)
        if not entries:
            return f"No menu found for {day_name}, {date_str}."
        msg_lines = [f"📅 Menu for {day_name}, {date_str}", ""]
        for meal in ["breakfast", "lunch", "dinner"]:
            meal_rows = [r for r in entries if r["meal_type"] == meal]
            if not meal_rows:
                continue
            row = meal_rows[0]
            header = MEAL_LABELS.get(meal, meal.capitalize())
            items_list = "\n  • " + "\n  • ".join([i.strip() for i in row["items"].split(",")])
            msg_lines.append(f"{header}:{items_list}")
            msg_lines.append("")  # blank line between meals
        return "\n".join(msg_lines).strip()


# ========= HANDLERS =========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Store chat_id in memory (for MVP single-user case)
    context.user_data["subscribed"] = True

    await update.message.reply_text(
        "👋 Hi! I'm your Mess Menu Agent.\n\n"
        "I can:\n"
        "• Send you menu before each meal automatically\n"
        "• Tell you today's or tomorrow's menu on request\n\n"
        "Commands:\n"
        "/today - Show today's full menu\n"
        "/tomorrow - Show tomorrow's menu\n"
        "/meal breakfast|lunch|dinner - Show today's specific meal\n\n"
        "✅ You are now subscribed for daily meal reminders."
    )

    # Schedule daily jobs for this user
    schedule_daily_jobs_for_user(context, chat_id)


def schedule_daily_jobs_for_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Schedule breakfast, lunch, and dinner reminders for this chat."""
    jq = context.job_queue

    # Clear previous jobs for this chat (MVP simple approach)
    for job in jq.get_jobs_by_name(f"breakfast_{chat_id}"):
        job.schedule_removal()
    for job in jq.get_jobs_by_name(f"lunch_{chat_id}"):
        job.schedule_removal()
    for job in jq.get_jobs_by_name(f"dinner_{chat_id}"):
        job.schedule_removal()

    # Breakfast at 8:00
    jq.run_daily(
        send_scheduled_meal,
        time=time(8, 0, tzinfo=IST),
        days=(0, 1, 2, 3, 4, 5, 6),
        name=f"breakfast_{chat_id}",
        data={"chat_id": chat_id, "meal_type": "breakfast"},
    )

    # Lunch at 13:00 (1 PM)
    jq.run_daily(
        send_scheduled_meal,
        time=time(13, 0, tzinfo=IST),
        days=(0, 1, 2, 3, 4, 5, 6),
        name=f"lunch_{chat_id}",
        data={"chat_id": chat_id, "meal_type": "lunch"},
    )

    # Dinner at 20:00 (8 PM)
    jq.run_daily(
        send_scheduled_meal,
        time=time(20, 0, tzinfo=IST),
        days=(0, 1, 2, 3, 4, 5, 6),
        name=f"dinner_{chat_id}",
        data={"chat_id": chat_id, "meal_type": "dinner"},
    )


async def send_scheduled_meal(context: ContextTypes.DEFAULT_TYPE):
    """Job callback: send the relevant meal menu."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    meal_type = job_data["meal_type"]

    weekday, date_obj = get_today_weekday()
    text = format_menu_message(weekday, date_obj, meal_type)
    await context.bot.send_message(chat_id=chat_id, text=text)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday, date_obj = get_today_weekday()
    text = format_menu_message(weekday, date_obj, None)
    await update.message.reply_text(text)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now_ist = datetime.now(IST)
    tomorrow_dt = now_ist + timedelta(days=1)
    weekday = tomorrow_dt.weekday()
    date_obj = tomorrow_dt.date()
    text = format_menu_message(weekday, date_obj, None)
    await update.message.reply_text(text)


async def meal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /meal breakfast|lunch|dinner")
        return

    meal_type = context.args[0].lower()
    if meal_type not in ["breakfast", "lunch", "dinner"]:
        await update.message.reply_text("Please choose one of: breakfast, lunch, dinner.")
        return

    weekday, date_obj = get_today_weekday()
    text = format_menu_message(weekday, date_obj, meal_type)
    await update.message.reply_text(text)


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """If user just types normal text like 'what's for dinner today?'."""
    msg = update.message.text.lower()
    weekday, date_obj = get_today_weekday()

    if "dinner" in msg:
        text = format_menu_message(weekday, date_obj, "dinner")
    elif "lunch" in msg:
        text = format_menu_message(weekday, date_obj, "lunch")
    elif "breakfast" in msg:
        text = format_menu_message(weekday, date_obj, "breakfast")
    else:
        text = (
            "I didn't fully understand 😅\n\n"
            "Try commands like:\n"
            "/today\n"
            "/tomorrow\n"
            "/meal breakfast\n"
            "/meal lunch\n"
            "/meal dinner"
        )
    await update.message.reply_text(text)


# ========= MAIN =========

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("meal", meal))

    # Fallback for free-text questions
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
