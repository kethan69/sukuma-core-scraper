import sqlite3
import json
import csv
import os

DB_NAME = "scraper_vault.db"
SHARED_DIR = "/data/data/com.termux/files/home/storage/shared/Download"

def export_data():
    if not os.path.exists(DB_NAME):
        print("[!] Database vault not found. Run scraper.py first.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT quote, author, timestamp FROM scraped_items")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[!] Vault is currently empty. No records to export.")
        return

    # Ensure shared storage directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)

    json_path = os.path.join(SHARED_DIR, "client_export.json")
    csv_path = os.path.join(SHARED_DIR, "client_export.csv")

    # Format data records
    records = []
    for row in rows:
        records.append({
            "quote": row[0],
            "author": row[1],
            "timestamp": row[2]
        })

    # 1. Export to JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"[+] JSON Export saved: {json_path}")

    # 2. Export to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Quote", "Author", "Timestamp"])
        for r in records:
            writer.writerow([r["quote"], r["author"], r["timestamp"]])
    print(f"[+] CSV Export saved: {csv_path}")

if __name__ == "__main__":
    export_data()
