from src.filter_logic import get_actionable_games
from src.database import setup_db, set_rejected_price, update_last_notified
import pytest


def test_get_actionable_games(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    wishlist = [
        {"appid": 1, "name": "G1", "discount_pct": 50, "price_usd": 4.0},  # Valid
        {"appid": 2, "name": "G2", "discount_pct": 20, "price_usd": 3.0},  # Failed: discount < 50
        {"appid": 3, "name": "G3", "discount_pct": 60, "price_usd": 6.0},  # Failed: price > 5.0
        {"appid": 4, "name": "G4", "discount_pct": 75, "price_usd": 2.0},  # Failed: owned by family
        {"appid": 5, "name": "G5", "discount_pct": 50, "price_usd": 4.0},  # Failed: rejected price
        {"appid": 6, "name": "G6", "discount_pct": 50, "price_usd": 4.0},  # Failed: already notified at this price
    ]

    family_games = {4}
    set_rejected_price(db_path, 5, 4.0)
    update_last_notified(db_path, 6, 4.0)

    results = get_actionable_games(wishlist, family_games, db_path)
    assert len(results) == 1
    assert results[0]['appid'] == 1


def test_get_actionable_games_lower_than_rejected_and_notified(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)

    # If price drops further than previous rejection or notification, it should be actionable
    wishlist = [
        {"appid": 10, "name": "G10", "discount_pct": 75, "price_usd": 2.5},  # Previously rejected at 4.0
        {"appid": 20, "name": "G20", "discount_pct": 80, "price_usd": 2.0},  # Previously notified at 4.0
    ]

    set_rejected_price(db_path, 10, 4.0)
    update_last_notified(db_path, 20, 4.0)

    results = get_actionable_games(wishlist, set(), db_path)
    assert len(results) == 2
    appids = [r['appid'] for r in results]
    assert 10 in appids
    assert 20 in appids
