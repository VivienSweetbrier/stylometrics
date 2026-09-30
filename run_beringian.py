import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

target_dbs = ['athabaskan', 'nganasan', 'kalevala', 'yukaghir', 'inuit', 'mari', 'sami', 'uralic', 'samoyedic']
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
        else:
            return None
            
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
    if freq:
        all_freqs[db.stem] = freq

print(f"Loaded {len(all_freqs)} databases for the Beringian/Uralic expedition.")

all_tags = set()
for freqs in all_freqs.values():
    all_tags.update(freqs.keys())
all_tags = sorted(list(all_tags))

names = list(all_freqs.keys())
matrix = []
for name in names:
    matrix.append([all_freqs[name].get(t, 0.0) for t in all_tags])
matrix = np.array(matrix)

sim_matrix = cosine_similarity(matrix)

report = "# Forensic Antiquity Engine: The Beringian-Uralic Expedition\n\n"
report += "Mapping the syntactic decay across the deep Eurasian-American continuum, specifically focusing on the Samoyedic (Nganasan), Uralic (Kalevala), and Na-Dene (Athabaskan) bridges.\n\n"
report += "## Syntactic Similarity Matrix (Cosine Similarity of Morphological Fingerprints)\n\n"

results = []
for i in range(len(names)):
    for j in range(i+1, len(names)):
        sim = ((sim_matrix[i][j] + 1) / 2) * 100
        results.append((names[i], names[j], sim))

results.sort(key=lambda x: x[2], reverse=True)

for r in results:
    report += f"- **{r[0].upper()}** vs **{r[1].upper()}** : {r[2]:.2f}%\n"

with open("notebooks/beringian_uralic_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Report generated.")
