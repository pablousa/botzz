import os
import json
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5482557625  # <-- COLOCA SEU ID AQUI

USERS_FILE = "users.json"
GIFTS_FILE = "giftcards.json"

# ---------------- DATA ----------------
def load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

users = load(USERS_FILE)
gifts = load(GIFTS_FILE)

def ensure_user(uid):
    if uid not in users:
        users[uid] = {"balance": 0}

# ---------------- COUNTRIES ----------------
COUNTRIES = {
    "USA": {"price": 1200, "flag": "🇺🇸"},
    "Germany": {"price": 900, "flag": "🇩🇪"},
    "UK": {"price": 950, "flag": "🇬🇧"},
    "Brazil": {"price": 400, "flag": "🇧🇷"},
    "Argentina": {"price": 300, "flag": "🇦🇷"},
    "India": {"price": 200, "flag": "🇮🇳"},
}

# ---------------- UTILS ----------------
def generate_key():
    return "".join(random.choices(string.ascii_letters + string.digits, k=30))

def generate_gift_code():
    return "GIFT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Zeus Key System\n\n"
        "💰 Use /saldo\n"
        "🛒 Use /loja\n"
        "🎁 Use /resgatar CODIGO"
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    await update.message.reply_text(f"💰 Balance: {users[uid]['balance']} ZC")

# ---------------- LOJA ----------------
async def loja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for name, data in COUNTRIES.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{data['flag']} {name} - {data['price']} ZC",
                callback_data=f"buy_{name}"
            )
        ])

    await update.message.reply_text(
        "🛒 Choose a country:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- COMPRA ----------------
async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    ensure_user(uid)

    country = query.data.split("_")[1]
    item = COUNTRIES.get(country)

    if not item:
        return

    if users[uid]["balance"] < item["price"]:
        await query.edit_message_text("❌ Not enough ZC.")
        return

    users[uid]["balance"] -= item["price"]

    key = generate_key()

    save(USERS_FILE, users)

    await query.edit_message_text(
        f"🔑 Key Generated\n\n"
        f"🌍 Country: {item['flag']} {country}\n"
        f"🔐 Key: {key}\n\n"
        f"✅ Delivered successfully"
    )

# ---------------- GIFT ----------------
async def resgatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)

    if not context.args:
        await update.message.reply_text("Use /resgatar CODIGO")
        return

    code = context.args[0]

    if code not in gifts or gifts[code]["used"]:
        await update.message.reply_text("❌ Invalid or already used.")
        return

    value = gifts[code]["value"]
    gifts[code]["used"] = True

    users[uid]["balance"] += value

    save(USERS_FILE, users)
    save(GIFTS_FILE, gifts)

    await update.message.reply_text(f"🎉 Redeemed! +{value} ZC")

# ---------------- ADMIN ----------------
async def gerar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Use /gerar VALOR")
        return

    value = int(context.args[0])

    code = generate_gift_code()
    gifts[code] = {"value": value, "used": False}

    save(GIFTS_FILE, gifts)

    await update.message.reply_text(f"🎁 Gift created:\n{code} = {value} ZC")

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("loja", loja))
    app.add_handler(CommandHandler("resgatar", resgatar))
    app.add_handler(CommandHandler("gerar", gerar))

    app.add_handler(CallbackQueryHandler(buy_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
