# Steam Discount Watchdog 🎮🕵️‍♂️

A lightweight, automated Python Telegram Bot that monitors your Steam Wishlist and alerts you of *deep discounts* (e.g., under $5.00 and 50%+ off). Designed to run 24/7 on a server (like PythonAnywhere) to ensure you never miss a great deal, without bothering you with minor 10% sales.

## Why This Bot?

Steam already sends emails when games go on sale, but if you have hundreds of games on your wishlist, you'll be spammed with alerts for games that only dropped from $60 to $50. 

**Steam Discount Watchdog** applies strict, customizable filter rules before sending you a notification:
1. **Price Limit:** The game must cost less than **$5.00**.
2. **Discount Limit:** The game must be at least **50% off**.
3. **Family Library Check:** Automatically checks if your Steam Family members already own the game. If they do, you don't need to buy it!
4. **Smart Memory:** Keeps track of prices using an SQLite database. If a game stays on sale, you won't be spammed every day.
5. **Interactive UI:** Provides inline Telegram buttons to instantly "Okay" to dismiss the notification, or "Reject Price" if you think the game is still too expensive at that specific price point, permanently muting it until it goes even lower.

*Note: The bot uses a smart fallback technique to bypass Steam's recent removal of the public JSON wishlist API, ensuring 100% reliability by querying the Steam Web API directly.*

## Architecture

- **Language:** Python 3.10+
- **Database:** SQLite3 (No ORM, lightweight, serverless)
- **Telegram Bot API:** `python-telegram-bot` (v20+) with `JobQueue` for scheduling.
- **Steam API:** Utilizes Steam Web API (`IWishlistService` and `appdetails`) with smart rate-limit avoidance (1.5s sleeps).

## Prerequisites

You need the following environment variables set up:
- `TELEGRAM_TOKEN`: Your bot token from [@BotFather](https://t.me/botfather).
- `TELEGRAM_CHAT_ID`: Your personal Telegram Chat ID.
- `STEAM_API_KEY`: Your Steam API Key.
- `MAIN_STEAM_ID`: Your SteamID64.
- `FAMILY_STEAM_IDS`: A comma-separated list of your family members' SteamID64s (e.g., `1111,2222,3333`).

## Local Setup & Testing

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SteamDiscountWatchdog.git
   cd SteamDiscountWatchdog
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Export the required environment variables:
   ```bash
   export TELEGRAM_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   export STEAM_API_KEY="your_api_key"
   export MAIN_STEAM_ID="your_steam_id"
   export FAMILY_STEAM_IDS="family_id_1,family_id_2"
   ```
4. Run the bot:
   ```bash
   python -m src.main
   ```

## Configuration

You can easily adjust the hardcoded limits in `src/filter_logic.py`:
- `MAX_PRICE_USD = 5.00`
- `MIN_DISCOUNT_PCT = 50`

## Contributing

Feel free to open issues or submit pull requests. If you want to add support for multiple currencies or dynamic user registration via Telegram commands, PRs are welcome!

## License

MIT License. Do whatever you want with it!

