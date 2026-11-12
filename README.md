# Steam Discount Watchdog 🎮

A Python bot that reads a Steam wishlist and sends a Telegram digest on each run. Games with discounts of 21% or more get individual deal cards. The digest lists the other games with their current prices in euros and shows discounts of 1–20%.

## Local run on Windows

From the repository root in PowerShell:

```powershell
python -m pip install -r requirements.txt
$env:TELEGRAM_TOKEN = "<your bot token>"
$env:TELEGRAM_CHAT_ID = "<your chat ID>"
$env:MAIN_STEAM_ID = "<your SteamID64>"
python -m src.main
```

## AWS Lambda

Use `src.main.lambda_handler` as the handler. Include `src/` and the installed dependencies from `requirements.txt` at the package root. Set the three environment variables listed above and configure Amazon EventBridge Scheduler to invoke the function once a day.

Set the Lambda timeout for the size of your wishlist. The Steam parser makes a separate price request for each game and pauses 1.5 seconds between requests.
