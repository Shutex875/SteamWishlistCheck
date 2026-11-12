from src.database import get_all_game_states

MIN_DISCOUNT_PCT = 21


def get_actionable_games(
    wishlist: list[dict],
    family_games: set[int],
    db_path: str,
) -> list[dict]:
    states = get_all_game_states(db_path)
    actionable = []
    for game in wishlist:
        if game['appid'] in family_games:
            continue
        if game['discount_pct'] < MIN_DISCOUNT_PCT:
            continue

        price = game['price']
        state = states.get(game['appid'], {})
        rejected = state.get('rejected_price')
        if rejected is not None and price >= rejected:
            continue

        last_notified = state.get('last_notified_price')
        if last_notified is not None and price == last_notified:
            continue

        actionable.append(game)
    return actionable

