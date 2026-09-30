import os
import requests
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class MasterScraper:
    def __init__(self):
        self.sources = {
            "ETCBC": "https://github.com/ETCBC/bhsa/archive/refs/heads/master.zip",
            "Perseus": "https://github.com/PerseusDL/canonical-greekLit/archive/refs/heads/master.zip",
            "ORACC": "http://oracc.museum.upenn.edu/cams/gkab/corpusjson/Q000039.json",
            "QuranicCorpus": "http://corpus.quran.com/download/quranic-corpus-morphology-0.4.xml",
            "TITUS": "https://titus.uni-frankfurt.de/texte/etcs/iran/airan/avesta/avest.htm",
            "CAL": "http://cal.huc.edu/search/mandaic_dump.txt" # Mock endpoint for script structure
        }

    def scrape_all(self):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print("Starting Global Academic Data Scrape (SSL Bypassed)...")
        for name, url in self.sources.items():
            print(f"[{name}] Initiating connection to {url}...")
            try:
                # Bypass SSL Verification
                response = requests.get(url, timeout=30, stream=True, verify=False)
                if response.status_code == 200:
                    file_path = DATA_DIR / f"{name}_raw.dat"
                    downloaded_size = 0
                    max_size = 5 * 1024 * 1024 # 5 MB cap for testing
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                if downloaded_size > max_size:
                                    print("  -> Reached 5MB cap. Truncating download for engine test.")
                                    break
                    print(f"  -> Success. Downloaded {downloaded_size/1024:.1f} KB to {file_path.name}")
                else:
                    print(f"  -> Failed. Status Code: {response.status_code}")
            except Exception as e:
                print(f"  -> Connection Error: {str(e)}")

        print("\nScraping phase complete.")

if __name__ == "__main__":
    scraper = MasterScraper()
    scraper.scrape_all()
