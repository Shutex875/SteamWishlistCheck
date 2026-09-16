from src.database import get_last_notified, get_rejected_price


def get_actionable_games(wishlist: list[dict], family_games: set[int], db_path: str) -> list[dict]:
    actionable = []
    for game in wishlist:
        if game['appid'] in family_games:
            continue
        if game['discount_pct'] < 50:
            continue
        if game['price_usd'] > 5.0:
            continue

        rejected = get_rejected_price(db_path, game['appid'])
        if rejected is not None and game['price_usd'] >= rejected:
            continue

        last_notified = get_last_notified(db_path, game['appid'])
        if last_notified is not None and game['price_usd'] == last_notified:
            continue

        actionable.append(game)
    return actionable
