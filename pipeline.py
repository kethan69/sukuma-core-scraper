import sqlite3
import time
import random
import json
import csv
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DB_NAME = "scraper_vault.db"
JSON_EXPORT = "client_export.json"
CSV_EXPORT = "client_export.csv"
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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

def run_pipeline():
    print("[+] Initializing Unified Sukuma Pipeline...")
    
    # 1. Database Initialization
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

    # 2. Scrape & Ingest Phase with Jitter
    try:
        delay = random.uniform(2.0, 5.0)
        print(f"[*] Applying anti-bot jitter: waiting {delay:.2f}s...")
        time.sleep(delay)

        response = requests.get(TARGET_URL, headers=get_stealth_headers(), timeout=15)
        if response.status_code != 200:
            print(f"[-] Target responded with status code: {response.status_code}")
            conn.close()
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        containers = soup.select('.quote') or soup.select('div.item')
        print(f"[+] Discovered {len(containers)} records on target page.")

        new_entries = 0
        for container in containers:
            title_elem = container.select_one('.text') or container.find(text=True)
            author_elem = container.select_one('.author')
            tag_elems = container.select('.tags .tag')

            title = title_elem.get_text(strip=True) if title_elem else "N/A"
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            tags = ", ".join([t.get_text(strip=True) for t in tag_elems])

            if title == "N/A":
                continue

            item_hash = str(hash(title + author))
            cursor.execute("SELECT id FROM extracted_items WHERE item_hash = ?", (item_hash,))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO extracted_items (item_hash, title, author, tags, scraped_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item_hash, title, author, tags, datetime.now().isoformat()))
                new_entries += 1

        conn.commit()
        print(f"[+] Ingestion complete. Added {new_entries} new unique rows.")

    except Exception as e:
        print(f"[-] Scraping phase error: {e}")

    # 3. Direct Export Phase (Atomic & Guaranteed Schema Match)
    try:
        cursor.execute("SELECT title, author, tags, scraped_at FROM extracted_items")
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "title": row[0],
                "author": row[1],
                "tags": row[2],
                "scraped_at": row[3]
            })

        # Write JSON Artifact
        with open(JSON_EXPORT, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)

        # Write CSV Artifact
        with open(CSV_EXPORT, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Author", "Tags", "Scraped At"])
            for item in items:
                writer.writerow([item["title"], item["author"], item["tags"], item["scraped_at"]])

        print(f"[+] Successfully generated atomic exports: {len(items)} records written.")

    except Exception as e:
        print(f"[-] Export phase error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_pipeline()
