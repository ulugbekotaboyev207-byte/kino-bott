import logging
import os
import re

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import database as db

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ADMIN_IDS = set(
    int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom!\n\n"
        "Instagramdagi videoning raqamini yuboring, men sizga to'liq videoni jo'nataman.\n\n"
        "Masalan: 1"
    )


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not re.fullmatch(r"\d+", text):
        await update.message.reply_text(
            "Iltimos, faqat raqam yuboring. Masalan: 1"
        )
        return

    file_id = db.get_video(text)

    if file_id:
        await update.message.reply_video(
            video=file_id,
            caption=f"Video #{text}",
        )
    else:
        await update.message.reply_text(
            f"{text}-raqamli video topilmadi.\n"
            "Raqamni tekshirib qaytadan yuboring."
        )


async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    video = update.message.video
    caption = (update.message.caption or "").strip()

    if not video:
        return

    if not re.fullmatch(r"\d+", caption):
        await update.message.reply_text(
            "Video caption(izoh)ida faqat raqam bo'lishi kerak.\n"
            "Masalan, videoni yuborishda captionga: 1"
        )
        return

    db.add_video(caption, video.file_id)
    await update.message.reply_text(
        f"{caption}-raqamli video saqlandi!\n"
        f"Jami videolar: {db.count_videos()} ta"
    )


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text("Foydalanish: /delete <raqam>")
        return

    number = context.args[0]
    if db.delete_video(number):
        await update.message.reply_text(f"{number}-raqamli video o'chirildi.")
    else:
        await update.message.reply_text(f"{number}-raqamli video topilmadi.")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    videos = db.list_all()
    if not videos:
        await update.message.reply_text("Hozircha hech qanday video saqlanmagan.")
        return

    numbers = ", ".join(row[0] for row in videos)
    await update.message.reply_text(
        f"Saqlangan videolar ({len(videos)} ta):\n{numbers}"
    )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning Telegram ID: {update.effective_user.id}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi! Environment variable sifatida BOT_TOKEN ni belgilang."
        )

    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid_command))

    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("list", list_command))

    app.add_handler(MessageHandler(filters.VIDEO, handle_admin_video))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
