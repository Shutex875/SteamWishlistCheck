import requests
import time
import logging

DEFAULT_TIMEOUT = 10

def fetch_owned_games(steam_id: str, api_key: str) -> set[int]:
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json"
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if "response" in data and "games" in data["response"]:
            return {g["appid"] for g in data["response"]["games"]}
        return set()
    except Exception as e:
        logging.error(f"Failed to fetch owned games for {steam_id}: {e}")
        return set()

def fetch_wishlist(steam_id: str) -> list[dict]:
    parsed = []

    # 1. Получаем список ID игр из твоего вишлиста через надежный API
    wishlist_url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid={steam_id}"

    try:
        logging.info(f"Fetching wishlist IDs for {steam_id}...")
        resp = requests.get(wishlist_url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("response", {}).get("items", [])
        if not items:
            logging.info("Wishlist is empty or inaccessible.")
            return []

        appids = [str(item["appid"]) for item in items]
        logging.info(f"Found {len(appids)} games. Fetching PT prices...")

        # 2. Запрашиваем цены для найденных игр
        for appid in appids:
            price_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=price_overview,basic&cc=PT"

            try:
                p_resp = requests.get(price_url, timeout=DEFAULT_TIMEOUT)
                p_resp.raise_for_status()
                p_data = p_resp.json()

                game_data = p_data.get(appid, {})
                if not game_data.get("success"):
                    continue

                data = game_data.get("data", {})
                name = data.get("name", "Unknown Game")
                is_free = data.get("is_free", False)
                price_overview = data.get("price_overview", {})

                if is_free:
                    parsed.append({
                        "appid": int(appid),
                        "name": name,
                        "is_discounted": True,
                        "discount_pct": 100,
                        "price": 0.0,
                        "original_price": 0.0,
                        "url": f"https://store.steampowered.com/app/{appid}/"
                    })
                    continue

                if not price_overview:
                    continue

                discount_pct = price_overview.get("discount_percent", 0)
                price = price_overview.get("final", 0) / 100.0
                original_price = price / (1 - (discount_pct / 100.0)) if 0 < discount_pct < 100 else 0.0

                parsed.append({
                    "appid": int(appid),
                    "name": name,
                    "is_discounted": discount_pct > 0,
                    "discount_pct": discount_pct,
                    "price": round(price, 2),
                    "original_price": round(original_price, 2),
                    "url": f"https://store.steampowered.com/app/{appid}/"
                })
            except Exception as e:
                logging.error(f"Error fetching price for appid {appid}: {e}")
            finally:
                time.sleep(1.5)

    except Exception as e:
        logging.error(f"Error fetching wishlist IDs for {steam_id}: {e}")

    logging.info(f"Successfully parsed {len(parsed)} games with PT prices.")
    return parsed