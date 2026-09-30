import os
import urllib.request
import json
from pathlib import Path

def download_corpus():
    base_dir = Path(r"c:\Users\Vivian\Desktop\Synoptics\data\raw\historical_corpus")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Federalist Papers
    fed_url = "https://www.gutenberg.org/cache/epub/18/pg18.txt"
    fed_path = base_dir / "federalist_papers.txt"
    try:
        urllib.request.urlretrieve(fed_url, fed_path)
        print("Downloaded Federalist Papers")
    except Exception as e:
        print(f"Failed to download Federalist Papers: {e}")
        # Try alternate URL
        try:
            fed_url_alt = "https://www.gutenberg.org/files/18/18-0.txt"
            urllib.request.urlretrieve(fed_url_alt, fed_path)
            print("Downloaded Federalist Papers (alt)")
        except Exception as e2:
            print(f"Failed to download Federalist Papers (alt): {e2}")

    # 2. Bixby Letter
    bixby_text = """Executive Mansion,
Washington, Nov. 21, 1864.

Dear Madam,

I have been shown in the files of the War Department a statement of the Adjutant General of Massachusetts that you are the mother of five sons who have died gloriously on the field of battle.

I feel how weak and fruitless must be any word of mine which should attempt to beguile you from the grief of a loss so overwhelming. But I cannot refrain from tendering you the consolation that may be found in the thanks of the Republic they died to save.

I pray that our Heavenly Father may assuage the anguish of your bereavement, and leave you only the cherished memory of the loved and lost, and the solemn pride that must be yours to have laid so costly a sacrifice upon the altar of freedom.

Yours, very sincerely and respectfully,

A. Lincoln"""
    
    bixby_path = base_dir / "bixby_letter.txt"
    bixby_path.write_text(bixby_text, encoding="utf-8")
    print("Saved Bixby Letter")
    
    # 3. QAnon Drops (stub)
    q_drops = [
        {
            "drop_id": 1,
            "timestamp": "2017-10-28T14:33:00Z",
            "text": "HRC extradition already in motion effective yesterday with several countries in case of cross border run. Passport approved to be flagged effective 10/30 @ 12:01am.",
            "tripcode": "!ITPb.qbhqo"
        },
        {
            "drop_id": 2,
            "timestamp": "2017-10-28T15:15:00Z",
            "text": "Mockingbird\nHRC detained, not arrested (yet).\nWhere is Huma? Follow Huma.",
            "tripcode": "!ITPb.qbhqo"
        }
    ]
    q_path = base_dir / "qanon_drops.json"
    q_path.write_text(json.dumps(q_drops, indent=4), encoding="utf-8")
    print("Saved QAnon drops stub")

if __name__ == "__main__":
    download_corpus()
