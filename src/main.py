import logging
import os
from collections.abc import Iterator
from html import escape

import requests

from src.steam_api import fetch_wishlist

MIN_DISCOUNT_PCT = 21
TELEGRAM_TEXT_LIMIT = 4096
NO_BIG_SALES = "😴 Спи спокойно, Санечек! Сегодня в вишлисте без громких распродаж."
WISHLIST_LABEL = "Твой вишлист:"

logging.basicConfig(level=logging.INFO)


def format_sale_message(game: dict) -> str | None:
    discount = game['discount_pct']
    if discount < MIN_DISCOUNT_PCT:
        return None
    if discount <= 50:
        title = "👀 Взгляни-ка, неплохое предложение!"
    elif discount <= 80:
        title = "🔥 Санечек, беги покупай!"
    elif discount <= 90:
        title = "🚀 Санечка, лети покупай!"
    else:
        title = "🎁 Халява! Глянь до чего дождались:"

    return (
        f"{title}\n\n"
        f"🎮 {game['name']}\n\n"
        f"💰 Было: {game['original_price']:.2f} € 💸 Стало: {game['price']:.2f} € "
        f"📉 Скидка: −{discount}%\n\n"
        f"🔗 Купить в Steam: {game['url']}"
    )


def wishlist_blocks(games: list[dict], has_sales: bool) -> Iterator[str]:
    heading = f"📋 <b>{WISHLIST_LABEL}</b>"
    heading_length = len(f"📋 {WISHLIST_LABEL}")
    lines = [heading] if has_sales else [NO_BIG_SALES, heading]
    length = heading_length if has_sales else len(NO_BIG_SALES) + 1 + heading_length
    max_line_length = TELEGRAM_TEXT_LIMIT - length - 1
    for game in games:
        discount = game["discount_pct"]
        suffix = f" (-{discount}%)" if discount > 0 else ""
        price = f" — {game['price']:.2f} €{suffix}"
        max_name_length = max_line_length - len(price) - len("• ")
        name = game["name"]
        if len(name) > max_name_length:
            name = name[:max_name_length - 1] + "…"
        line_length = 2 + len(name) + len(price)
        if length + 1 + line_length > TELEGRAM_TEXT_LIMIT:
            yield "\n".join(lines)
            lines = [heading]
            length = heading_length
        lines.append(f"• {escape(name)}{price}")
        length += 1 + line_length

    if not games:
        lines.append("• Список пуст.")
    yield "\n".join(lines)


def send_message(token: str, chat_id: str, text: str) -> None:
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
            },
            timeout=10,
        )
        response.raise_for_status()
        if not response.json().get("ok"):
            raise RuntimeError("Telegram rejected the message.")
    except requests.RequestException as error:
        # Requests exceptions can include the URL, which contains the bot token.
        raise RuntimeError(f"Telegram sendMessage failed ({type(error).__name__}).") from None


def lambda_handler(event, context):
    config = {
        name: os.environ.get(name)
        for name in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "MAIN_STEAM_ID")
    }
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    token = config["TELEGRAM_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    wishlist = fetch_wishlist(config["MAIN_STEAM_ID"])
    other_games = []
    sale_count = 0

    for game in wishlist:
        card = format_sale_message(game)
        if card is None:
            other_games.append(game)
        else:
            send_message(token, chat_id, escape(card))
            sale_count += 1

    if other_games or not sale_count:
        for block in wishlist_blocks(other_games, has_sales=bool(sale_count)):
            send_message(token, chat_id, block)

    logging.info("Sent wishlist digest for %d games (%d deals).", len(wishlist), sale_count)


if __name__ == "__main__":
    lambda_handler({}, None)
