import sqlite3
import json
import csv
import os

DB_NAME = "scraper_vault.db"

def export_data():
    if not os.path.exists(DB_NAME):
        print(f"[-] Database {DB_NAME} not found. Skipping export safely.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Dynamically check which tables exist in the vault
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    target_table = None
    if "extracted_items" in tables:
        target_table = "extracted_items"
    elif "scraped_items" in tables:
        target_table = "scraped_items"
        
    if not target_table:
        print("[-] No valid data tables found in SQLite vault. Safe exit.")
        conn.close()
        return

    # 2. Dynamically inspect column names to prevent schema mismatch crashes
    cursor.execute(f"PRAGMA table_info({target_table});")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"[+] Found table '{target_table}' with columns: {columns}")

    # 3. Build a safe, adaptive query based on available columns
    if "title" in columns and "author" in columns:
        query = "SELECT title, author, tags, scraped_at FROM extracted_items"
    elif "quote" in columns and "author" in columns:
        query = "SELECT quote, author, timestamp FROM scraped_items"
    else:
        # Fallback wildcard select
        query = f"SELECT * FROM {target_table}"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"[-] Query execution warning: {e}")
        conn.close()
        return
    
    items = []
    for row in rows:
        # Handle flexible length rows safely
        items.append({
            "title": row[1] if len(row) > 1 else "N/A",
            "author": row[2] if len(row) > 2 else "Unknown",
            "tags": row[3] if len(row) > 3 else "",
            "scraped_at": row[4] if len(row) > 4 else "N/A"
        })
        
    # Export to JSON
    with open("client_export.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4, ensure_ascii=False)
        
    # Export to CSV
    with open("client_export.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Author", "Tags", "Scraped At"])
        for item in items:
            writer.writerow([item["title"], item["author"], item["tags"], item["scraped_at"]])
            
    conn.close()
    print(f"[+] Bulletproof export complete: {len(items)} records packaged.")

if __name__ == "__main__":
    export_data()
