import requests


def fetch_owned_games(steam_id: str, api_key: str) -> set[int]:
    """Fetch the set of appids owned by the given steam_id.
    
    Handles private profiles and API errors gracefully by returning an empty set.
    """
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return set()
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "response" in data and "games" in data["response"]:
            games = data["response"]["games"]
            if isinstance(games, list):
                return {g["appid"] for g in games if isinstance(g, dict) and "appid" in g}
        return set()
    except Exception:
        # Gracefully handle private accounts or API errors
        return set()


def fetch_wishlist(steam_id: str) -> list[dict]:
    """Fetch public wishlist games for the given steam_id.
    
    Handles private profiles and API errors gracefully by returning an empty list.
    """
    # Wishlist data is paginated, but for simplicity we fetch page 0 which usually has 100+ items
    # In a full implementation, loop through pages
    url = f"https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/?p=0"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        resp.raise_for_status()
        data = resp.json()
        
        if not isinstance(data, dict):
            return []

        parsed = []
        for app_id_str, info in data.items():
            if not isinstance(info, dict):
                continue
            
            subs = info.get("subs", [])
            if not subs or not isinstance(subs, list):
                continue
                
            sub_0 = subs[0]
            if not isinstance(sub_0, dict):
                continue

            discount_pct = sub_0.get("discount_pct", 0) or 0
            raw_price = sub_0.get("price", 0) or 0
            try:
                price = float(raw_price) / 100.0  # Price is typically in cents in Steam API
            except (ValueError, TypeError):
                price = 0.0
            
            try:
                appid = int(app_id_str)
            except (ValueError, TypeError):
                continue

            parsed.append({
                "appid": appid,
                "name": info.get("name", "Unknown"),
                "discount_pct": discount_pct,
                "price_usd": price
            })
        return parsed
    except Exception:
        # Gracefully handle private accounts or API errors
        return []
