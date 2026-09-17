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
    try:
        url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid={steam_id}"
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        items = resp.json().get("response", {}).get("items", [])
        appids = [str(item["appid"]) for item in items]
        
        logging.info(f"Found {len(appids)} items on wishlist for {steam_id}. Fetching prices...")
        
        for appid in appids:
            details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=price_overview,basic"
            retries = 3
            while retries > 0:
                d_resp = requests.get(details_url, timeout=DEFAULT_TIMEOUT)
                if d_resp.status_code == 429:
                    logging.warning(f"Rate limited by Steam on appid {appid}. Sleeping for 60s...")
                    time.sleep(60)
                    retries -= 1
                    continue
                    
                if d_resp.status_code != 200:
                    break
                    
                try:
                    d_data = d_resp.json()
                    if d_data and str(appid) in d_data and d_data[str(appid)].get("success"):
                        data = d_data[str(appid)].get("data", {})
                        price_overview = data.get("price_overview")
                        if price_overview:
                            discount_pct = price_overview.get("discount_percent", 0)
                            price = price_overview.get("final", 0) / 100.0
                            name = data.get("name", "Unknown Game")
                            
                            parsed.append({
                                "appid": int(appid),
                                "name": name,
                                "is_discounted": discount_pct > 0,
                                "discount_pct": discount_pct,
                                "price_usd": price
                            })
                except Exception as e:
                    logging.error(f"Error parsing appdetails for {appid}: {e}")
                
                break
            time.sleep(1.5)
    except Exception as e:
        logging.error(f"Error fetching wishlist for {steam_id}: {e}")
        
    return parsed

