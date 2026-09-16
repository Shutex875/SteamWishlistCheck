import asyncio
import logging
import os
import sys
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from src.bot import create_app
from src.database import clear_expired_sales, setup_db, update_last_notified
from src.filter_logic import get_actionable_games
from src.steam_api import fetch_owned_games, fetch_wishlist

logging.basicConfig(level=logging.INFO)


async def check_wishlist_periodic(context):
    db_path = context.job.data['db_path']
    steam_id = context.job.data['steam_id']
    steam_api_key = context.job.data['steam_api_key']
    family_ids = context.job.data['family_ids']
    chat_id = context.job.data['chat_id']
    bot: Bot = context.bot

    logging.info("Running periodic wishlist check...")

    try:
        wishlist = await asyncio.to_thread(fetch_wishlist, steam_id)

        family_games = set()
        for f_id in family_ids:
            games = await asyncio.to_thread(fetch_owned_games, f_id, steam_api_key)
            family_games.update(games)

        actionable = get_actionable_games(wishlist, family_games, db_path)

        for game in actionable:
            try:
                text = f"🎮 {game['name']} is on sale!\nDiscount: {game['discount_pct']}%\nPrice: ${game['price_usd']}"
                keyboard = [
                    [InlineKeyboardButton("Fiyatı Beğenmedim", callback_data=f"reject_{game['appid']}_{game['price_usd']}")],
                    [InlineKeyboardButton("Tamam (Sil)", callback_data="delete_msg")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
                update_last_notified(db_path, game['appid'], game['price_usd'])
            except Exception as e:
                logging.error(f"Failed to send deal notification for game {game.get('appid')}: {e}", exc_info=True)

        # Clear expired
        discounted_ids = [g['appid'] for g in wishlist if g.get('discount_pct', 0) > 0]
        clear_expired_sales(db_path, discounted_ids)
    except Exception as e:
        logging.error(f"Error during periodic wishlist check: {e}", exc_info=True)
        return


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    steam_id = os.environ.get("MAIN_STEAM_ID")
    steam_api_key = os.environ.get("STEAM_API_KEY")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    family_ids_str = os.environ.get("FAMILY_STEAM_IDS", "")
    family_ids = [f.strip() for f in family_ids_str.split(",") if f.strip()] if family_ids_str else []
    db_path = os.environ.get("DB_PATH", "data.db")

    missing = []
    if not token:
        missing.append("TELEGRAM_TOKEN")
    if not steam_id:
        missing.append("MAIN_STEAM_ID")
    if not steam_api_key:
        missing.append("STEAM_API_KEY")
    if not chat_id:
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    setup_db(db_path)

    app = create_app(token, db_path)

    # Schedule wishlist check every 24 hours (86400 seconds)
    job_queue = app.job_queue
    job_queue.run_repeating(
        check_wishlist_periodic,
        interval=86400,
        first=10,
        data={
            'db_path': db_path,
            'steam_id': steam_id,
            'steam_api_key': steam_api_key,
            'family_ids': family_ids,
            'chat_id': chat_id,
        },
    )

    # Run polling
    logging.info("Bot starting polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
