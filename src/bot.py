import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from src.database import set_rejected_price

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started! I will monitor your wishlist.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "delete_msg":
        logging.info("Deleting message on user request")
        await query.message.delete()
        return

    if data.startswith("reject_"):
        try:
            parts = data.split("_")
            app_id = int(parts[1])
            price = float(parts[2])
        except (ValueError, IndexError) as e:
            logging.warning(f"Failed to parse reject callback data '{data}': {e}")
            return

        db_path = context.bot_data['db_path']
        set_rejected_price(db_path, app_id, price)
        logging.info(f"Rejected price set to ${price} for game {app_id}")
        keyboard = [[InlineKeyboardButton("Okay", callback_data="delete_msg")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Rejected price set to ${price} for game {app_id}. You won't see it again at this price!",
            reply_markup=reply_markup
        )


def create_app(token: str, db_path: str) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data['db_path'] = db_path

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    return app
