"""
Telegram bot that sells individual photos, unlocked with Telegram Stars.

Flow:
  - Admin replies to a photo with /addphoto <price> <description> to add it to the catalog.
  - Users run /gallery to browse. Locked photos are shown blurred (spoiler) with an
    "Unlock for X⭐" button.
  - Tapping the button sends a Telegram Stars invoice (native payment, no bank/provider needed).
  - On successful payment, the bot immediately sends the full, unblurred photo and
    remembers the purchase so the user isn't charged again.
  - /myphotos re-sends anything the user has already bought, for free.
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputPaidMediaPhoto,
    LabeledPrice,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

import database as db

# Load .env from project root first; fall back to .venv/.env if root is missing
# or contains the placeholder token.
root_env = Path(__file__).resolve().parent / ".env"
venv_env = Path(__file__).resolve().parent / ".venv" / ".env"
load_dotenv(root_env)
root_token = os.getenv("BOT_TOKEN")
if (
    not root_token
    or root_token == "123456789:AAExampleTokenGoesHere"
    or root_token.startswith("123456789:AAExample")
):
    load_dotenv(venv_env, override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
if CHANNEL_ID and CHANNEL_ID.isdigit():
    CHANNEL_ID = int(CHANNEL_ID)

ADMIN_IDS = {
    int(x)
    for x in os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")).replace(" ", "").split(",")
    if x
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ---------------------------------------------------------------------------
# Basic commands
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Use /gallery to browse photos available to unlock with Telegram Stars ⭐\n"
        "Use /myphotos to see photos you've already bought."
    )


async def gallery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photos = db.list_unpurchased_photos(user_id)

    if not photos:
        await update.message.reply_text(
            "No locked photos left for you right now — check /myphotos, "
            "or ask the admin to add more."
        )
        return

    for photo in photos:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                f"🔓 Unlock for {photo['price']} ⭐",
                callback_data=f"buy_{photo['id']}",
            )]]
        )
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo["file_id"],
            caption=f"{photo['description']}\n\nPrice: {photo['price']} ⭐",
            has_spoiler=True,
            reply_markup=keyboard,
        )


async def my_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photos = db.list_purchased_photos(user_id)

    if not photos:
        await update.message.reply_text("You haven't unlocked any photos yet. Try /gallery.")
        return

    for photo in photos:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo["file_id"],
            caption=photo["description"],
        )


# ---------------------------------------------------------------------------
# Admin: add / remove photos
# ---------------------------------------------------------------------------

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You're not authorized to do that.")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "Reply to a photo with:\n/addphoto <price_in_stars> <description>"
        )
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: reply to a photo with /addphoto <price_in_stars> <description>"
        )
        return

    try:
        price = int(args[0])
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Price must be a positive whole number of Stars.")
        return

    description = " ".join(args[1:])
    file_id = update.message.reply_to_message.photo[-1].file_id  # largest size

    photo_id = db.add_photo(file_id, price, description, user_id)

    await update.message.reply_text(
        f"✅ Added photo #{photo_id} — \"{description}\" for {price} ⭐"
    )

    if CHANNEL_ID:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                f"🔓 Unlock for {price} ⭐",
                callback_data=f"buy_{photo_id}",
            )]]
        )
        paid_media = InputPaidMediaPhoto(media=file_id)
        await context.bot.send_paid_media(
            chat_id=CHANNEL_ID,
            star_count=price,
            media=[paid_media],
            caption=f"{description}\n\nPrice: {price} ⭐",
            reply_markup=keyboard,
            payload=f"photo_{photo_id}",
        )


async def remove_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You're not authorized to do that.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /removephoto <id>")
        return

    try:
        photo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Photo id must be a number.")
        return

    db.delete_photo(photo_id)
    await update.message.reply_text(f"🗑️ Removed photo #{photo_id} (if it existed).")


async def list_photos_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You're not authorized to do that.")
        return

    photos = db.list_all_photos()
    if not photos:
        await update.message.reply_text("Catalog is empty.")
        return

    lines = [f"#{p['id']} — {p['description']} — {p['price']} ⭐" for p in photos]
    await update.message.reply_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Payments (Telegram Stars)
# ---------------------------------------------------------------------------

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    photo_id = int(query.data.split("_", 1)[1])
    photo = db.get_photo(photo_id)

    if not photo:
        await query.message.reply_text("Sorry, that photo is no longer available.")
        return

    user_id = query.from_user.id
    if db.has_purchased(user_id, photo_id):
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=photo["file_id"],
            caption=f"You already own this one!\n{photo['description']}",
        )
        return

    # Telegram Stars payments: currency must be "XTR", provider_token is empty.
    # Amount is the number of Stars directly (no minor-unit multiplication).
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=photo["description"][:32] or "Unlock photo",
        description=f"Unlock full-resolution photo: {photo['description']}",
        payload=f"photo_{photo_id}",
        provider_token="",  # empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(label=photo["description"][:32] or "Photo", amount=photo["price"])],
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    # Always approve unless you have your own validation (e.g. stock check).
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload  # "photo_<id>"

    try:
        photo_id = int(payload.split("_", 1)[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Payment received, but something went wrong finding your photo.")
        return

    user_id = update.effective_user.id
    photo = db.get_photo(photo_id)

    db.record_purchase(user_id, photo_id)

    if not photo:
        await update.message.reply_text("Payment received, but that photo no longer exists.")
        return

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo["file_id"],
        caption=f"🎉 Unlocked!\n{photo['description']}",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set. Put it in your .env file.")

    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gallery", gallery))
    app.add_handler(CommandHandler("myphotos", my_photos))
    app.add_handler(CommandHandler("addphoto", add_photo))
    app.add_handler(CommandHandler("removephoto", remove_photo))
    app.add_handler(CommandHandler("listphotos", list_photos_admin))

    app.add_handler(CallbackQueryHandler(buy_callback, pattern=r"^buy_\d+$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    logger.info("Bot starting...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling()


if __name__ == "__main__":
    main()
