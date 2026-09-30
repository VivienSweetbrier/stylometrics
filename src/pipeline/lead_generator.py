import feedparser
import csv
import os
import datetime
from pathlib import Path

# Justia Dockets RSS Feeds for specific Nature of Suit (NOS) codes
RSS_FEEDS = {
    "Copyright": "https://dockets.justia.com/search?nos=820&cases=mostrecent&format=rss",
    "Trademark": "https://dockets.justia.com/search?nos=840&cases=mostrecent&format=rss",
    "Contract_Breach": "https://dockets.justia.com/search?nos=190&cases=mostrecent&format=rss",
    "Trade_Secrets": "https://dockets.justia.com/search?nos=880&cases=mostrecent&format=rss"
}

KEYWORDS = [
    "copyright infringement",
    "trade secret",
    "misappropriation",
    "breach of contract",
    "disputed document",
    "forgery",
    "fraud",
    "plagiarism"
]

def scan_dockets_for_leads(output_csv="legal_leads.csv"):
    """
    Scans Justia Federal Court Dockets via RSS to find brand new 
    lawsuits matching our target legal forensics keywords.
    """
    print("="*60)
    print("TRUTHVECTOR: AUTOMATED LEGAL LEAD GENERATOR")
    print("="*60)
    print("Scanning Federal Court Dockets for new IP/Contract cases...\n")
    
    leads = []
    
    for category, url in RSS_FEEDS.items():
        print(f"[*] Parsing feed: {category}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            title = entry.title.lower()
            summary = entry.summary.lower() if hasattr(entry, 'summary') else ""
            
            # Since we are querying specific NOS feeds (like 820 Copyright), 
            # EVERY case in this feed is a potential lead.
            # We will use keywords just to highlight the exceptionally hot leads.
            matched_keywords = [kw for kw in KEYWORDS if kw in title or kw in summary]
            
            leads.append({
                "Date": entry.published if hasattr(entry, 'published') else datetime.datetime.now().strftime("%Y-%m-%d"),
                "Category": category,
                "Case Name": entry.title,
                "Hot Lead": "YES" if matched_keywords else "NO",
                "Link": entry.link
            })
                
    if not leads:
        print("\n[!] No new cases matching targeted keywords found today.")
        return
        
    print(f"\n[+] Found {len(leads)} high-probability leads. Exporting to {output_csv}...")
    
    file_exists = os.path.isfile(output_csv)
    
    with open(output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Date", "Category", "Case Name", "Hot Lead", "Link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        for lead in leads:
            writer.writerow(lead)
            
    print("[SUCCESS] Leads saved to CSV. Your target defense attorneys are listed in these dockets.")

if __name__ == "__main__":
    scan_dockets_for_leads()
