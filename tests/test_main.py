from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from telegram import InlineKeyboardMarkup
from src.database import get_last_notified, setup_db, update_last_notified
from src.main import check_wishlist_periodic, main


@pytest.mark.asyncio
async def test_check_wishlist_periodic(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    context = MagicMock()
    context.job.data = {
        'db_path': db_path,
        'steam_id': '12345',
        'steam_api_key': 'key_abc',
        'family_ids': ['fam1', 'fam2'],
        'chat_id': 'chat_999',
    }
    context.bot.send_message = AsyncMock()

    mock_wishlist = [
        {'appid': 10, 'name': 'Game 10', 'discount_pct': 75, 'price_usd': 4.99},
        {'appid': 20, 'name': 'Game 20', 'discount_pct': 0, 'price_usd': 19.99},
        {'appid': 30, 'name': 'Game 30', 'discount_pct': 60, 'price_usd': 3.99},
    ]

    def mock_fetch_owned(f_id, api_key):
        if f_id == 'fam1':
            return {99}
        return {88}

    with patch('src.main.fetch_wishlist', return_value=mock_wishlist) as mock_fetch_wl, \
         patch('src.main.fetch_owned_games', side_effect=mock_fetch_owned) as mock_fetch_owned_patch, \
         patch('src.main.get_actionable_games') as mock_actionable:

        # Let's say only Game 10 is actionable
        mock_actionable.return_value = [
            {'appid': 10, 'name': 'Game 10', 'discount_pct': 75, 'price_usd': 4.99}
        ]

        await check_wishlist_periodic(context)

        mock_fetch_wl.assert_called_once_with('12345')
        assert mock_fetch_owned_patch.call_count == 2
        mock_actionable.assert_called_once_with(mock_wishlist, {99, 88}, db_path)

        # Verify message sent
        context.bot.send_message.assert_awaited_once()
        call_kwargs = context.bot.send_message.call_args.kwargs
        assert call_kwargs['chat_id'] == 'chat_999'
        assert "Game 10 is on sale!" in call_kwargs['text']
        assert "75%" in call_kwargs['text']
        assert "$4.99" in call_kwargs['text']

        # Verify keyboard markup
        markup = call_kwargs['reply_markup']
        assert isinstance(markup, InlineKeyboardMarkup)
        buttons = markup.inline_keyboard
        assert len(buttons) == 2
        assert buttons[0][0].text == "Fiyatı Beğenmedim"
        assert buttons[0][0].callback_data == "reject_10_4.99"
        assert buttons[1][0].text == "Tamam (Sil)"
        assert buttons[1][0].callback_data == "delete_msg"

        # Verify DB updated
        assert get_last_notified(db_path, 10) == 4.99


@pytest.mark.asyncio
async def test_check_wishlist_periodic_clears_expired(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    # Pre-populate DB with an older sale that is no longer discounted
    update_last_notified(db_path, 999, 2.99)
    assert get_last_notified(db_path, 999) == 2.99

    context = MagicMock()
    context.job.data = {
        'db_path': db_path,
        'steam_id': '12345',
        'steam_api_key': 'key_abc',
        'family_ids': [],
        'chat_id': 'chat_999',
    }
    context.bot.send_message = AsyncMock()

    # Wishlist has no discounted games
    mock_wishlist = [
        {'appid': 999, 'name': 'Old Game', 'discount_pct': 0, 'price_usd': 9.99}
    ]

    with patch('src.main.fetch_wishlist', return_value=mock_wishlist), \
         patch('src.main.get_actionable_games', return_value=[]):

        await check_wishlist_periodic(context)

        context.bot.send_message.assert_not_awaited()
        # Expired sale should have last_notified_price set to NULL
        assert get_last_notified(db_path, 999) is None


@pytest.mark.asyncio
async def test_check_wishlist_periodic_no_actionable(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    context = MagicMock()
    context.job.data = {
        'db_path': db_path,
        'steam_id': '12345',
        'steam_api_key': 'key_abc',
        'family_ids': [],
        'chat_id': 'chat_999',
    }
    context.bot.send_message = AsyncMock()

    with patch('src.main.fetch_wishlist', return_value=[]), \
         patch('src.main.get_actionable_games', return_value=[]):

        await check_wishlist_periodic(context)

        context.bot.send_message.assert_not_awaited()


def test_main():
    env_vars = {
        "TELEGRAM_TOKEN": "bot_token_123",
        "MAIN_STEAM_ID": "steam_111",
        "STEAM_API_KEY": "api_key_222",
        "TELEGRAM_CHAT_ID": "chat_333",
        "FAMILY_STEAM_IDS": "fam_1, fam_2",
    }

    mock_app = MagicMock()
    mock_job_queue = MagicMock()
    mock_app.job_queue = mock_job_queue

    with patch.dict('os.environ', env_vars, clear=True), \
         patch('src.main.setup_db') as mock_setup_db, \
         patch('src.main.create_app', return_value=mock_app) as mock_create_app:

        main()

        mock_setup_db.assert_called_once_with("data.db")
        mock_create_app.assert_called_once_with("bot_token_123", "data.db")
        mock_job_queue.run_repeating.assert_called_once_with(
            check_wishlist_periodic,
            interval=86400,
            first=10,
            data={
                'db_path': "data.db",
                'steam_id': "steam_111",
                'steam_api_key': "api_key_222",
                'family_ids': ["fam_1", "fam_2"],
                'chat_id': "chat_333",
            }
        )
        mock_app.run_polling.assert_called_once()


def test_main_empty_family_ids():
    env_vars = {
        "TELEGRAM_TOKEN": "bot_token_123",
        "MAIN_STEAM_ID": "steam_111",
        "STEAM_API_KEY": "api_key_222",
        "TELEGRAM_CHAT_ID": "chat_333",
        "FAMILY_STEAM_IDS": "",
    }

    mock_app = MagicMock()
    mock_job_queue = MagicMock()
    mock_app.job_queue = mock_job_queue

    with patch.dict('os.environ', env_vars, clear=True), \
         patch('src.main.setup_db'), \
         patch('src.main.create_app', return_value=mock_app):

        main()

        call_args = mock_job_queue.run_repeating.call_args
        assert call_args.kwargs['data']['family_ids'] == []
