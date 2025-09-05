import requests
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from telegram_alert import TelegramAlert


URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
GAIN = 10

telegram_alert = None

def get_last_date(date_str):
    parts = date_str.strip().split("-")
    if len(parts) == 2:
        return parts[1].strip()
    return parts[0].strip()


def normalize_date(date_str):
    current_year = datetime.now().year
    parts = date_str.split()
    if len(parts) != 2:
        return None

    day, month = parts
    month = month[:3]  # keep first 3 letters
    clean_date = f"{day} {month} {current_year}"

    try:
        return datetime.strptime(clean_date, "%d %b %Y")
    except ValueError:
        return None


def send_alert(message):
    """Lazy load TelegramAlert and send a message."""
    global telegram_alert
    if telegram_alert is None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            logging.error("⚠️ Telegram credentials not set. Skipping alert.")
            return
        telegram_alert = TelegramAlert(bot_token=bot_token, chat_id=chat_id)
    telegram_alert.send(message)


def main():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        logging.error(f"No table found on page {URL}")
        send_alert(f"No table found on page {URL}")
        return

    rows = table.find_all("tr")
    today = datetime.now().date()

    for row in rows[1:]:  # skip header
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if len(cols) < 3:
            continue

        ipo_name = cols[0]
        gmp = cols[3]
        date_col = cols[4]

        last_date_str = get_last_date(date_col)
        last_date = normalize_date(last_date_str)

        if not last_date:
            continue

        if last_date.date() == today:
            if "%" in gmp:
                try:
                    gain = int(gmp.replace("%", "").strip())
                    if gain >= GAIN:
                        message = f"{ipo_name} | Gain: {gain}%"
                        logging.info(message)
                        send_alert(message)
                except ValueError:
                    continue


if __name__ == "__main__":
    main()
