import requests
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from telegram_alert import TelegramAlert

URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
GAIN = 10

telegram_alert = None

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def get_last_date(date_str):
    logging.debug(f"Parsing last date from string: {date_str}")
    parts = date_str.strip().split("-")
    if len(parts) == 2:
        return parts[1].strip()
    return parts[0].strip()

def normalize_date(date_str):
    logging.debug(f"Normalizing date: {date_str}")
    current_year = datetime.now().year
    parts = date_str.split()
    if len(parts) != 2:
        logging.warning(f"Date string not in expected format: {date_str}")
        return None

    day, month = parts
    month = month[:3]  # keep first 3 letters
    clean_date = f"{day} {month} {current_year}"

    try:
        parsed = datetime.strptime(clean_date, "%d %b %Y")
        logging.debug(f"Normalized date: {parsed}")
        return parsed
    except ValueError as e:
        logging.error(f"Failed to parse date '{clean_date}': {e}")
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
        logging.info("Initializing TelegramAlert...")
        telegram_alert = TelegramAlert(bot_token=bot_token, chat_id=chat_id)

    logging.info(f"Sending alert: {message}")
    telegram_alert.send(message)

def main():
    logging.info(f"Fetching data from {URL}")
    try:
        resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch page: {e}")
        send_alert(f"Failed to fetch IPO page: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        logging.error(f"No table found on page {URL}")
        send_alert(f"No table found on page {URL}")
        return

    rows = table.find_all("tr")
    today = datetime.now().date()
    logging.info(f"Processing {len(rows)-1} rows (excluding header). Today={today}")

    for row in rows[1:]:  # skip header
        try:
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cols) < 5:
                logging.debug(f"Skipping row with insufficient columns: {cols}")
                continue

            ipo_name = cols[0]
            gmp = cols[3]
            date_col = cols[4]

            logging.debug(f"Row: IPO={ipo_name}, GMP={gmp}, DateCol={date_col}")

            last_date_str = get_last_date(date_col)
            last_date = normalize_date(last_date_str)

            if not last_date:
                logging.debug(f"Skipping IPO {ipo_name} due to invalid date.")
                continue

            if last_date.date() == today:
                try:
                    gain = float(gmp.replace("%", "").strip())
                    logging.debug(f"Parsed gain={gain} for IPO {ipo_name}")
                    if gain >= GAIN:
                        message = f"{ipo_name} | Gain: {gain}%"
                        logging.info(f"✅ Condition met: {message}")
                        send_alert(message)
                    else:
                        logging.debug(f"IPO {ipo_name} skipped: gain {gain}% < {GAIN}%")
                except ValueError:
                    logging.warning(f"Could not parse GMP value '{gmp}' for IPO {ipo_name}")
                    continue
        except Exception as error:
            logging.error(f"Error in row {row}: {error}")

if __name__ == "__main__":
    main()
