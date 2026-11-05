import sys
import json
import time
import requests
from bs4 import BeautifulSoup

def scrape_target(target_url):
    payload = []
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    print(f"[-] Target acquired: {target_url}")
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=(5, 10))
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Generic extraction example: grabbing all paragraphs or headings as a baseline
        # (You customize selectors per client)
        for elem in soup.select('p')[:10]:
            text = elem.get_text(strip=True)
            if text:
                payload.append({
                    "content": text,
                    "source_url": target_url,
                    "timestamp": int(time.time())
                })
                
        return payload
    except Exception as e:
        print(f"[!] Scraping failed: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[-] Usage: python flexible_scraper.py <URL>")
        sys.exit(1)
        
    url_to_scrape = sys.argv[1]
    data = scrape_target(url_to_scrape)
    
    if data:
        with open("client_dynamic_export.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"[+] Successfully extracted {len(data)} records for client deliverable.")
