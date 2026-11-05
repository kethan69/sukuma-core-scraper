import json
import time
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "9249714611:AAEi_q2bHduRZiChP_0bY-rYnYmeIaTuvSg"
TELEGRAM_CHAT_ID = "8555517035"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass  # Fail silently so network hiccups never block the pipeline

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def execute_scrape():
    payload = []
    page = 1
    
    while page <= 2:
        url = f"http://quotes.toscrape.com/page/{page}/"
        print(f"[-] Requesting: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=(5, 10))
            if response.status_code == 404:
                break
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.select('.quote')
            
            if not containers:
                break

            for container in containers:
                text_elem = container.select_one('.text')
                author_elem = container.select_one('.author')

                if text_elem and author_elem:
                    payload.append({
                        "quote": text_elem.get_text(strip=True),
                        "author": author_elem.get_text(strip=True),
                        "timestamp": int(time.time())
                    })
            
            page += 1
            time.sleep(0.5)

        except Exception as err:
            print(f"[!] Exception: {err}")
            break
            
    return payload

if __name__ == "__main__":
    data = execute_scrape()
    
    if data:
        target_file = "scraped_data.json"
        try:
            with open(target_file, "r") as f:
                store = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            store = []

        store.extend(data)

        with open(target_file, "w") as f:
            json.dump(store, f, indent=2)
            
        success_msg = f"*[Scraper Success]* Ingested `{len(data)}` records."
        print(f"[+] {success_msg}")
        send_telegram_alert(success_msg)
    else:
        print("[!] Ingestion returned zero records.")
