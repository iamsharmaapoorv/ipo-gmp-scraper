import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"

def get_last_date(date_str):
    """
    Extracts the last date from strings like:
    - '1-3 Sept' -> '3 Sept'
    - '3 Sept' -> '3 Sept'
    """
    parts = date_str.strip().split("-")
    if len(parts) == 2:
        return parts[1].strip()
    return parts[0].strip()

def normalize_date(date_str):
    """
    Converts '1 Sept' or '1 September' → datetime object with current year
    by normalizing month to its first 3 letters.
    """
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


def main():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find table
    table = soup.find("table")
    if not table:
        print("No table found on page")
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

        # print(f"{ipo_name} {gmp} {date_col}")

        last_date_str = get_last_date(date_col)
        last_date = normalize_date(last_date_str)

        # print(f"{last_date_str} {last_date} ")

        if not last_date:
            continue

        # Check if last date matches today
        if last_date.date() == today:
            # Extract % gain (e.g. "12%" -> 12)
            if "%" in gmp:
                try:
                    gain = int(gmp.replace("%", "").strip())
                    if gain >= 10:
                        print(f"{ipo_name} | Gain: {gain}%")
                except ValueError:
                    continue

if __name__ == "__main__":
    main()
