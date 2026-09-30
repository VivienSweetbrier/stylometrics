import sys
import time
import datetime
import numpy as np
from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.data_loader.sec_edgar_ingestor import SECEdgarIngestor
from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

# Configure Logging
log_file = BASE_DIR / "alpha_daemon.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# In production, this would be hooked up to AWS SES, SendGrid, or a Discord/Slack Webhook.
def send_private_alert(ticker, date, delta):
    alert_msg = f"CRITICAL GHOSTING ALERT: {ticker} | Date: {date} | Delta: {delta:.4f}"
    print(f"\n{'='*50}\n[PRIVATE ALERT] {alert_msg}\n{'='*50}\n")
    logging.warning(alert_msg)
    # Example Webhook integration:
    # requests.post("YOUR_DISCORD_WEBHOOK_URL", json={"content": alert_msg})

def process_ticker(ticker, ingestor, threshold=0.15):
    logging.info(f"Scanning {ticker}...")
    try:
        filings = ingestor.get_recent_8k_filings(ticker, limit=15)
        
        if len(filings) < 3:
            logging.info(f"[{ticker}] Insufficient filings to build a baseline.")
            return

        newest_filing = filings[0]
        historical_filings = filings[1:]
        
        baseline_texts = []
        for f in historical_filings:
            text = ingestor.fetch_filing_text(f['url'])
            if len(text) > 500:
                baseline_texts.append(text)
                
        if not baseline_texts:
            logging.info(f"[{ticker}] Could not extract sufficient text for baseline.")
            return

        hmm = BulletproofHMMGraph()
        hmm.train("\n\n".join(baseline_texts))
        
        base_scores = []
        for txt in baseline_texts:
            score, _ = hmm.calculate_log_likelihood(txt[:5000])
            if score != float('-inf'):
                base_scores.append(score)
                
        avg_base = np.mean(base_scores) if base_scores else 0
        
        newest_text = ingestor.fetch_filing_text(newest_filing['url'])
        score_new, _ = hmm.calculate_log_likelihood(newest_text[:5000])
        
        if score_new == float('-inf'):
            return

        delta = abs(avg_base - score_new)
        logging.info(f"[{ticker}] Base: {avg_base:.4f} | New: {score_new:.4f} | Delta: {delta:.4f}")
        
        if delta >= threshold:
            send_private_alert(ticker, newest_filing['date'], delta)
            
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")

def run_daemon(tickers, interval_hours=6):
    print("Initializing AlphaVector SEC EDGAR Daemon...")
    print(f"Logging to: {log_file}")
    ingestor = SECEdgarIngestor()
    
    while True:
        print(f"\n[{datetime.datetime.now()}] Starting scan cycle for {len(tickers)} tickers...")
        for ticker in tickers:
            print(f"Processing {ticker}...", end=" ", flush=True)
            process_ticker(ticker, ingestor)
            print("Done.")
            
            # Sleep to avoid aggressively hammering the SEC API and getting IP banned
            time.sleep(2)
            
        print(f"Cycle complete. Sleeping for {interval_hours} hours...")
        logging.info(f"Cycle complete. Sleeping for {interval_hours} hours.")
        
        # Sleep until the next cycle
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    # Test watchlist containing companies with recent volatility/PR activity
    WATCHLIST = [
        "INTC", "TSLA", "BA", "DIS", "AAPL", 
        "NVDA", "META", "AMZN", "NFLX", "GOOGL"
    ]
    
    try:
        # For testing purposes, we'll set interval to 24 hours. 
        run_daemon(WATCHLIST, interval_hours=24)
    except KeyboardInterrupt:
        print("\nDaemon terminated by user.")
