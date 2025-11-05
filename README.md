# IPO GMP Scraper

Python script to fetch IPO Grey Market Premium (GMP) data and filter IPOs 
that end today with >=10% gain.

Env variable needed:

  For telegram alert
```
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
```

## Usage
python3 ipo_gmp.py
