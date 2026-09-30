import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

target_dbs = ['ainu', 'andamanese', 'elamite', 'guanche', 'san', 'etruscan', 'tocharian', 'homer', 'mesopotamian', 'piraha']
DB_DIR = Path("data/processed")
dbs = [db for db in DB_DIR.glob("*.db") if any(t == db.stem.lower() for t in target_dbs)]

def get_pos_freq(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        if not c.fetchone(): return None
        c.execute("PRAGMA table_info(words)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'pos' in columns:
            query = "SELECT pos FROM words WHERE pos IS NOT NULL AND pos != ''"
        else: return None
            
        c.execute(query)
        rows = c.fetchall()
        conn.close()
        
        if not rows: return None
        tags = [r[0] for r in rows]
        counter = Counter(tags)
        total = len(tags)
        return {k: v/total for k, v in counter.items()}
    except:
        return None

all_freqs = {}
for db in dbs:
    freq = get_pos_freq(db)
    if freq: all_freqs[db.stem] = freq

all_tags = set()
for freqs in all_freqs.values(): all_tags.update(freqs.keys())
all_tags = sorted(list(all_tags))

names = list(all_freqs.keys())
matrix = np.array([[all_freqs[name].get(t, 0.0) for t in all_tags] for name in names])
sim_matrix = cosine_similarity(matrix)

report = "# The Deep Global Isolates\n\n"
report += "Testing the oldest, most genetically and linguistically isolated cultures on Earth against each other to search for a pre-historic baseline syntax.\n\n"

for target in ['ainu', 'andamanese', 'guanche', 'san', 'elamite']:
    if target in names:
        idx = names.index(target)
        results = []
        for i, name in enumerate(names):
            if name != target:
                sim = ((sim_matrix[idx][i] + 1) / 2) * 100
                results.append((name, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        
        report += f"## {target.upper()} Mythological Alignment\n"
        for r in results:
            report += f"- **{target.upper()}** vs **{r[0].upper()}** : {r[1]:.2f}%\n"
        report += "\n"

with open("notebooks/deep_isolates_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Done")
