import os
import email
from email import policy
import sys
from pathlib import Path
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import the forensic engine
from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

def parse_email_file(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        msg = email.message_from_file(f, policy=policy.default)
        
    date_str = msg.get('Date')
    try:
        # e.g., Wed, 13 Dec 2000 07:05:00 -0800 (PST)
        date_obj = email.utils.parsedate_to_datetime(date_str)
    except Exception:
        date_obj = None
        
    body = msg.get_payload()
    if type(body) == list:
        body = body[0].get_payload()
        
    return date_obj, body

def main():
    print("====================================================")
    print(" ENRON GHOSTING & FORENSIC ANALYSIS (ALPHAVECTOR) ")
    print("====================================================")
    
    target_dirs = [
        Path("data/raw/enron/skilling-j/sent"),
        Path("data/raw/enron/skilling-j/_sent_mail"),
        Path("data/raw/enron/skilling-j/sent_items")
    ]
    
    baseline_texts = []
    crisis_texts = []
    baseline_dates = []
    crisis_dates = []
    
    print("Parsing Skilling's Outbox...")
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for filename in os.listdir(target_dir):
            file_path = target_dir / filename
            if file_path.is_file():
                date_obj, body = parse_email_file(file_path)
                if date_obj and body and len(body.split()) > 20: # Only substantial emails
                    # Skilling resigned in August 2001. We define crisis as anything after June 2001
                    if date_obj.year < 2001 or (date_obj.year == 2001 and date_obj.month < 6):
                        baseline_texts.append(body)
                        baseline_dates.append(date_obj)
                    elif date_obj.year == 2001 and date_obj.month >= 6:
                        crisis_texts.append(body)
                        crisis_dates.append(date_obj)
                        
    print(f"Found {len(baseline_texts)} baseline emails (Pre-June 2001).")
    print(f"Found {len(crisis_texts)} crisis emails (Post-June 2001).")
    
    if len(baseline_texts) == 0 or len(crisis_texts) == 0:
        print("Not enough data to run the analysis.")
        return

    print("\nTraining HMM on Executive Baseline (Grammatical DNA)...")
    hmm = BulletproofHMMGraph()
    # Train on first 300 baseline emails to avoid taking too long
    train_text = "\n\n".join(baseline_texts[:300])
    hmm.train(train_text)
    print("Training complete.")
    
    print("\nScoring Baseline Set (Control Group)...")
    results = []
    
    # Score a sample of the baseline to establish normal
    for i, body in enumerate(baseline_texts[:50]):
        score, _ = hmm.calculate_log_likelihood(body)
        if score != float('-inf'):
            results.append({
                "Date": baseline_dates[i],
                "Period": "Pre-Crisis (Baseline)",
                "Log-Likelihood Score": score
            })
            
    print("\nScoring Crisis Set (Test Group)...")
    for i, body in enumerate(crisis_texts[:50]):
        score, _ = hmm.calculate_log_likelihood(body)
        if score != float('-inf'):
            results.append({
                "Date": crisis_dates[i],
                "Period": "Crisis (Ghosting Window)",
                "Log-Likelihood Score": score
            })
            
    df = pd.DataFrame(results)
    df = df.sort_values(by="Date")
    
    print("\n--- RESULTS ---")
    avg_base = df[df["Period"] == "Pre-Crisis (Baseline)"]["Log-Likelihood Score"].mean()
    avg_crisis = df[df["Period"] == "Crisis (Ghosting Window)"]["Log-Likelihood Score"].mean()
    
    print(f"Average Baseline Match Score: {avg_base:.4f}")
    print(f"Average Crisis Match Score:   {avg_crisis:.4f}")
    print(f"Stylistic Deviation (Delta):  {abs(avg_base - avg_crisis):.4f}")
    
    if avg_crisis < avg_base - 0.5:
        print("🚨 SEVERE DEVIATION DETECTED. The executive's style radically changed, indicating lawyer/PR scrubbing or mental check-out.")
    else:
        print("Style remained consistent.")

if __name__ == "__main__":
    main()
