import os
import email
from email import policy
import sys
from pathlib import Path
import datetime
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

def parse_email_file(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        msg = email.message_from_file(f, policy=policy.default)
    date_str = msg.get('Date')
    try:
        date_obj = email.utils.parsedate_to_datetime(date_str)
    except Exception:
        date_obj = None
    body = msg.get_payload()
    if type(body) == list:
        body = body[0].get_payload()
    return date_obj, body

target_dirs = [
    Path("data/raw/enron/lay-k/sent"),
    Path("data/raw/enron/lay-k/_sent"),
    Path("data/raw/enron/lay-k/sent_items")
]

baseline_texts = []
crisis_texts = []
for target_dir in target_dirs:
    if not target_dir.exists(): continue
    for filename in os.listdir(target_dir):
        file_path = target_dir / filename
        if file_path.is_file():
            date_obj, body = parse_email_file(file_path)
            if date_obj and body and len(body.split()) > 20:
                if date_obj.year < 2001 or (date_obj.year == 2001 and date_obj.month < 9):
                    baseline_texts.append(body)
                elif date_obj.year == 2001 and date_obj.month >= 9:
                    crisis_texts.append(body)

print(f"Lay Baseline: {len(baseline_texts)}")
print(f"Lay Crisis: {len(crisis_texts)}")

hmm = BulletproofHMMGraph()
hmm.train("\n\n".join(baseline_texts[:300]))

scores_base = [hmm.calculate_log_likelihood(b)[0] for b in baseline_texts[:50]]
scores_base = [s for s in scores_base if s != float('-inf')]
avg_base = np.mean(scores_base)

scores_crisis = [hmm.calculate_log_likelihood(b)[0] for b in crisis_texts[:50]]
scores_crisis = [s for s in scores_crisis if s != float('-inf')]
avg_crisis = np.mean(scores_crisis)

print(f"Avg Base: {avg_base:.4f}")
print(f"Avg Crisis: {avg_crisis:.4f}")
print(f"Delta: {abs(avg_base - avg_crisis):.4f}")
