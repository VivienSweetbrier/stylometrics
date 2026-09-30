import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.data_loader.sec_edgar_ingestor import SECEdgarIngestor
from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_sec_pipeline.py <TICKER>")
        sys.exit(1)
        
    ticker = sys.argv[1].upper()
    print("====================================================")
    print(f" SEC EDGAR AUTOMATED PIPELINE: {ticker}")
    print("====================================================")
    
    ingestor = SECEdgarIngestor()
    
    print(f"Querying SEC EDGAR for recent 8-K filings for {ticker}...")
    filings = ingestor.get_recent_8k_filings(ticker, limit=15)
    
    if len(filings) < 3:
        print(f"Not enough 8-K filings found for {ticker} to build a reliable baseline.")
        return
        
    print(f"Found {len(filings)} recent 8-K filings.")
    
    # The most recent filing is index 0. We'll use the rest as the baseline.
    newest_filing = filings[0]
    historical_filings = filings[1:]
    
    print("\nDownloading and parsing historical filings to build Grammatical DNA baseline...")
    baseline_texts = []
    for f in historical_filings:
        text = ingestor.fetch_filing_text(f['url'])
        if len(text) > 500: # Ensure it's not a tiny stub
            baseline_texts.append(text)
            
    if not baseline_texts:
        print("Could not extract sufficient text from historical filings.")
        return
        
    print(f"Successfully extracted {len(baseline_texts)} historical baselines.")
    
    hmm = BulletproofHMMGraph()
    hmm.train("\n\n".join(baseline_texts))
    
    print("\nScoring historical baseline set to establish 'normal' range...")
    base_scores = []
    for txt in baseline_texts:
        score, _ = hmm.calculate_log_likelihood(txt[:5000]) # chunk it to save time
        if score != float('-inf'):
            base_scores.append(score)
            
    avg_base = np.mean(base_scores) if base_scores else 0
    print(f"Historical Baseline Mean Conformity Score: {avg_base:.4f}")
    
    print(f"\nDownloading and parsing NEWEST 8-K ({newest_filing['date']})...")
    newest_text = ingestor.fetch_filing_text(newest_filing['url'])
    
    score_new, _ = hmm.calculate_log_likelihood(newest_text[:5000])
    
    print("\n--- RESULTS ---")
    print(f"Newest Filing Score: {score_new:.4f}")
    delta = abs(avg_base - score_new)
    print(f"Stylistic Deviation (Delta): {delta:.4f}")
    
    if delta > 0.15:
        print("\n🚨 AUTOMATED ALERT: SEVERE DEVIATION DETECTED.")
        print("This 8-K filing is structurally alien to the company's historical standard.")
        print("High probability of crisis PR intervention or significant internal structural changes.")
    else:
        print("\n✅ STATUS: NORMAL.")
        print("This 8-K filing aligns with the company's standard corporate grammatical structure.")

if __name__ == "__main__":
    main()
