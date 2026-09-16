import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram.ext import CommandHandler, CallbackQueryHandler, Application
from src.bot import start, button_callback, create_app
from src.database import setup_db, get_rejected_price


@pytest.mark.asyncio
async def test_start_handler():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await start(update, context)

    update.message.reply_text.assert_awaited_once_with("Bot started! I will monitor your wishlist.")


@pytest.mark.asyncio
async def test_button_callback_delete_msg():
    update = MagicMock()
    update.callback_query.data = "delete_msg"
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.delete = AsyncMock()
    context = MagicMock()

    await button_callback(update, context)

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.message.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_button_callback_reject(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    update = MagicMock()
    update.callback_query.data = "reject_730_14.99"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    context = MagicMock()
    context.bot_data = {'db_path': db_path}

    await button_callback(update, context)

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.edit_message_text.assert_awaited_once_with(
        text="Rejected price set to $14.99 for game 730. You won't see it again at this price!"
    )

    saved_price = get_rejected_price(db_path, 730)
    assert saved_price == 14.99


@pytest.mark.asyncio
async def test_button_callback_reject_malformed(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    update = MagicMock()
    update.callback_query.data = "reject_invalid"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    context = MagicMock()
    context.bot_data = {'db_path': db_path}

    await button_callback(update, context)

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.edit_message_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_button_callback_unknown_action():
    update = MagicMock()
    update.callback_query.data = "other_action"
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.delete = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    context = MagicMock()

    await button_callback(update, context)

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.message.delete.assert_not_awaited()
    update.callback_query.edit_message_text.assert_not_awaited()


def test_create_app(tmp_path):
    db_path = str(tmp_path / "bot.db")
    token = "test_token"

    app = create_app(token, db_path)

    assert isinstance(app, Application)
    assert app.bot_data['db_path'] == db_path

    registered_handlers = app.handlers.get(0, [])
    assert len(registered_handlers) == 2
    assert any(isinstance(h, CommandHandler) for h in registered_handlers)
    assert any(isinstance(h, CallbackQueryHandler) for h in registered_handlers)
