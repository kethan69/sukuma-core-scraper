import sqlite3
import json
import csv

DB_NAME = "scraper_vault.db"

def export_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query the correct table created by the hardened scraper engine
    cursor.execute("SELECT title, author, tags, scraped_at FROM extracted_items")
    rows = cursor.fetchall()
    
    # Format data into dictionaries
    items = []
    for row in rows:
        items.append({
            "title": row[0],
            "author": row[1],
            "tags": row[2],
            "scraped_at": row[3]
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
    print(f"[+] Successfully exported {len(items)} records to JSON and CSV.")

if __name__ == "__main__":
    export_data()
