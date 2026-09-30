import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

target_dbs = ['tocharian', 'etruscan', 'vedic', 'homer', 'norse', 'silkroad', 'mesopotamian', 'manichaean', 'gnostic_expansions', 'celtic', 'minoan', 'tartessian', 'thracian', 'roman']
DB_DIR = Path("data/processed")
dbs = [db for db in DB_DIR.glob("*.db") if any(t in db.name.lower() for t in target_dbs)]

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
        elif 'morph_tag' in columns:
            query = "SELECT morph_tag FROM words WHERE morph_tag IS NOT NULL AND morph_tag != ''"
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

report = "# Deep Eurasian Isolates: Tocharian & Etruscan\n\n"

# Process Tocharian
if 'tocharian' in names:
    toch_idx = names.index('tocharian')
    toch_results = []
    for i, name in enumerate(names):
        if name != 'tocharian':
            sim = ((sim_matrix[toch_idx][i] + 1) / 2) * 100
            toch_results.append((name, sim))
    toch_results.sort(key=lambda x: x[1], reverse=True)
    report += "## Tocharian Mythological Alignment\n"
    for r in toch_results:
        report += f"- **TOCHARIAN** vs **{r[0].upper()}** : {r[1]:.2f}%\n"
    report += "\n"

# Process Etruscan
if 'etruscan' in names:
    etr_idx = names.index('etruscan')
    etr_results = []
    for i, name in enumerate(names):
        if name != 'etruscan':
            sim = ((sim_matrix[etr_idx][i] + 1) / 2) * 100
            etr_results.append((name, sim))
    etr_results.sort(key=lambda x: x[1], reverse=True)
    report += "## Etruscan Mythological Alignment\n"
    for r in etr_results:
        report += f"- **ETRUSCAN** vs **{r[0].upper()}** : {r[1]:.2f}%\n"

with open("notebooks/tocharian_etruscan_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Done")
