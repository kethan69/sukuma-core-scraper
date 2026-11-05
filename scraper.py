import sqlite3
import time
import random
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION & COMPLIANCE ---
DB_NAME = "scraper_vault.db"
TARGET_URL = "https://quotes.toscrape.com/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
]

def get_stealth_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive"
    }

def init_vault():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extracted_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_hash TEXT UNIQUE,
            title TEXT,
            author TEXT,
            tags TEXT,
            scraped_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def resilient_extract(element):
    try:
        title_elem = (
            element.select_one('.text') or 
            element.select_one('span.quote-text') or 
            element.find(text=True)
        )
        title = title_elem.get_text(strip=True) if title_elem else "N/A"

        author_elem = (
            element.select_one('.author') or 
            element.select_one('.quote-author')
        )
        author = author_elem.get_text(strip=True) if author_elem else "Unknown"

        tag_elems = element.select('.tags .tag') or element.select('a.tag')
        tags = ", ".join([tag.get_text(strip=True) for tag in tag_elems])

        return {
            "title": title,
            "author": author,
            "tags": tags
        }
    except Exception as e:
        print(f"[-] Parsing exception caught: {e}")
        return None

def run_scraper():
    init_vault()
    print("[+] Initializing hardened scraping engine...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        delay = random.uniform(2.5, 6.0)
        print(f"[*] Applying anti-bot human jitter: pausing for {delay:.2f}s...")
        time.sleep(delay)

        response = requests.get(TARGET_URL, headers=get_stealth_headers(), timeout=15)
        
        if response.status_code != 200:
            print(f"[-] Request failed with status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        containers = soup.select('.quote') or soup.select('div.item')
        print(f"[+] Discovered {len(containers)} target records.")

        new_entries = 0
        for container in containers:
            data = resilient_extract(container)
            if not data or data['title'] == "N/A":
                continue

            item_hash = str(hash(data['title'] + data['author']))
            
            cursor.execute("SELECT id FROM extracted_items WHERE item_hash = ?", (item_hash,))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO extracted_items (item_hash, title, author, tags, scraped_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item_hash, data['title'], data['author'], data['tags'], datetime.now().isoformat()))
                new_entries += 1

        conn.commit()
        print(f"[!!] Ingestion completed. Added {new_entries} new unique records to the SQLite vault.")

    except Exception as e:
        print(f"[-] Critical execution error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_scraper()
