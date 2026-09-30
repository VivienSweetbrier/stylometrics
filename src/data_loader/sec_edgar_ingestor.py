import requests
import json
from bs4 import BeautifulSoup
import re
import time

class SECEdgarIngestor:
    def __init__(self, user_agent="AlphaVector Quant Engine (research@alphavector.com)"):
        # SEC requires a user-agent
        self.headers = {'User-Agent': user_agent}
        self.tickers_url = "https://www.sec.gov/files/company_tickers.json"
        self.submissions_url = "https://data.sec.gov/submissions/CIK{}.json"
        
        self.cik_map = self._load_tickers()

    def _load_tickers(self):
        try:
            r = requests.get(self.tickers_url, headers=self.headers)
            r.raise_for_status()
            data = r.json()
            # map ticker to CIK (padded to 10 digits)
            return {v['ticker'].upper(): str(v['cik_str']).zfill(10) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading SEC tickers: {e}")
            return {}

    def get_cik(self, ticker):
        return self.cik_map.get(ticker.upper())

    def get_recent_8k_filings(self, ticker, limit=10):
        cik = self.get_cik(ticker)
        if not cik:
            print(f"Ticker {ticker} not found in SEC database.")
            return []

        url = self.submissions_url.format(cik)
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            print(f"Failed to fetch submissions for {ticker} (CIK: {cik})")
            return []

        data = r.json()
        filings = data.get('filings', {}).get('recent', {})
        if not filings:
            return []

        forms = filings.get('form', [])
        accessions = filings.get('accessionNumber', [])
        primary_docs = filings.get('primaryDocument', [])
        report_dates = filings.get('reportDate', [])

        results = []
        for i, form in enumerate(forms):
            if form == '8-K':
                acc_no = accessions[i]
                acc_no_no_dashes = acc_no.replace('-', '')
                doc = primary_docs[i]
                date = report_dates[i]
                
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_no_dashes}/{doc}"
                results.append({
                    'date': date,
                    'url': doc_url,
                    'accession': acc_no
                })
                if len(results) >= limit:
                    break
                    
        return results

    def fetch_filing_text(self, url):
        time.sleep(0.1) # SEC rate limiting is 10 requests/sec
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            # Basic cleanup
            text = re.sub(r'\s+', ' ', text)
            return text
        return ""
