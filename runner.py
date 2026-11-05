import time
import subprocess
import sys

INTERVAL_SECONDS = 3600  # Set to 3600 for 1 hour interval (or change to 300 for 5-min testing)

def main():
    print("==================================================")
    print("  [Sukuma Core] Silicon Valley Pipeline Active   ")
    print("==================================================")
    
    while True:
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[+] [{timestamp_str}] Initiating scheduled ingestion cycle...")
        
        # 1. Execute core scraper
        try:
            subprocess.run([sys.executable, "scraper.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[!] Scraper execution encountered an issue: {e}")
            
        # 2. Trigger client export refresh
        try:
            subprocess.run([sys.executable, "export_utility.py"], check=True)
            print("[+] Client export files refreshed in shared Downloads storage.")
        except subprocess.CalledProcessError as e:
            print(f"[!] Export utility encountered an issue: {e}")
            
        print(f"[-] Node entering sleep mode for {INTERVAL_SECONDS} seconds...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
