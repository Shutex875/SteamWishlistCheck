from src.database import get_all_game_states


def get_actionable_games(
    wishlist: list[dict],
    family_games: set[int],
    db_path: str,
    min_discount_pct: int = 50,
    max_price_usd: float = 5.0,
) -> list[dict]:
    states = get_all_game_states(db_path)
    actionable = []
    for game in wishlist:
        if game['appid'] in family_games:
            continue
        if game['discount_pct'] < min_discount_pct:
            continue
        if game['price_usd'] > max_price_usd:
            continue

        state = states.get(game['appid'], {})
        rejected = state.get('rejected_price')
        if rejected is not None and game['price_usd'] >= rejected:
            continue

        last_notified = state.get('last_notified_price')
        if last_notified is not None and game['price_usd'] == last_notified:
            continue

        actionable.append(game)
    return actionable

