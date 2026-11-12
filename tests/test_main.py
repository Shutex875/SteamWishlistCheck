from unittest.mock import patch

import pytest

from src.main import NO_BIG_SALES, format_sale_message, lambda_handler


@pytest.mark.parametrize(("discount", "title"), [
    (0, None),
    (20, None),
    (21, "👀 Взгляни-ка, неплохое предложение!"),
    (50, "👀 Взгляни-ка, неплохое предложение!"),
    (51, "🔥 Санечек, беги покупай!"),
    (80, "🔥 Санечек, беги покупай!"),
    (81, "🚀 Санечка, лети покупай!"),
    (90, "🚀 Санечка, лети покупай!"),
    (91, "🎁 Халява! Глянь до чего дождались:"),
    (100, "🎁 Халява! Глянь до чего дождались:"),
])
def test_format_sale_message(discount, title):
    text = format_sale_message({
        'name': 'Game', 'discount_pct': discount, 'price': 4.5,
        'original_price': 20, 'url': 'https://store.steampowered.com/app/10/',
    })
    expected = None if title is None else (
        f"{title}\n\n🎮 Game\n\n"
        f"💰 Было: 20.00 € 💸 Стало: 4.50 € 📉 Скидка: −{discount}%\n\n"
        "🔗 Купить в Steam: https://store.steampowered.com/app/10/"
    )
    assert text == expected


@pytest.fixture
def config(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("MAIN_STEAM_ID", "456")


@pytest.mark.parametrize("discount", [20, 21])
def test_lambda_handler(config, discount):
    wishlist = [
        {"name": "Deal", "discount_pct": discount, "price": 4.5,
         "original_price": 5.7, "url": "https://store.steampowered.com/app/10/"},
        {"name": "A & <B>", "discount_pct": 1, "price": 10},
        {"name": "Full price", "discount_pct": 0, "price": 12.5},
    ]
    with patch("src.main.fetch_wishlist", return_value=wishlist) as fetch, \
         patch("src.main.requests.post") as post:
        post.return_value.json.return_value = {"ok": True}
        lambda_handler({}, None)

    fetch.assert_called_once_with("456")
    texts = [call.kwargs["json"]["text"] for call in post.call_args_list]
    assert post.call_args.args[0] == "https://api.telegram.org/bottest_token/sendMessage"
    assert post.call_args.kwargs["json"]["chat_id"] == "123"
    assert post.call_args.kwargs["json"]["parse_mode"] == "HTML"
    assert "• A &amp; &lt;B&gt; — 10.00 € (-1%)" in texts[-1]
    assert "• Full price — 12.50 €" in texts[-1]
    if discount == 21:
        assert texts == [format_sale_message(wishlist[0]), texts[-1]]
        assert "Deal" not in texts[-1]
    else:
        assert len(texts) == 1
        assert texts[0].startswith(NO_BIG_SALES)
        assert "• Deal — 4.50 € (-20%)" in texts[0]


def test_empty_wishlist(config):
    with patch("src.main.fetch_wishlist", return_value=[]), \
         patch("src.main.requests.post") as post:
        post.return_value.json.return_value = {"ok": True}
        lambda_handler({}, None)

    post.assert_called_once()
    assert post.call_args.kwargs["json"]["text"].startswith(NO_BIG_SALES)


def test_long_wishlist(config):
    wishlist = [{"name": "Game " + str(index), "discount_pct": 0, "price": 5}
                for index in range(500)]
    with patch("src.main.fetch_wishlist", return_value=wishlist), \
         patch("src.main.requests.post") as post:
        post.return_value.json.return_value = {"ok": True}
        lambda_handler({}, None)

    texts = [call.kwargs["json"]["text"] for call in post.call_args_list]
    assert len(texts) > 1
    assert all(len(text.replace("<b>", "").replace("</b>", "")) <= 4096 for text in texts)
    assert sum(text.count("• Game ") for text in texts) == len(wishlist)
