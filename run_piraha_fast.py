import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DB_DIR = Path("data/processed")
dbs = list(DB_DIR.glob("*.db"))

def get_pos_freq(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        if not c.fetchone():
            return None
            
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
        
        if not rows:
            return None
            
        tags = [r[0] for r in rows]
        counter = Counter(tags)
        total = len(tags)
        return {k: v/total for k, v in counter.items()}
    except Exception as e:
        print(f"Error reading {db_path.name}: {e}")
        return None

print("Extracting syntactic frequencies...")
all_freqs = {}
for db in dbs:
    freq = get_pos_freq(db)
    if freq:
        all_freqs[db.stem] = freq

if 'piraha' not in all_freqs:
    print("Piraha database not found or empty!")
    sys.exit(1)

print(f"Extracted syntax for {len(all_freqs)} traditions.")

# Build global feature set
all_tags = set()
for freqs in all_freqs.values():
    all_tags.update(freqs.keys())
all_tags = sorted(list(all_tags))

# Build matrix
matrix = []
names = list(all_freqs.keys())
for name in names:
    freqs = all_freqs[name]
    vec = [freqs.get(t, 0.0) for t in all_tags]
    matrix.append(vec)

matrix = np.array(matrix)
piraha_idx = names.index('piraha')
piraha_vec = matrix[piraha_idx].reshape(1, -1)

# Compute cosine similarity against all
similarities = cosine_similarity(piraha_vec, matrix)[0]

results = []
for i, name in enumerate(names):
    if name == 'piraha':
        continue
    sim = ((similarities[i] + 1) / 2) * 100
    results.append({'target': name.upper(), 'similarity': sim})

results.sort(key=lambda x: x['similarity'], reverse=True)

report = "# The Null-Hypothesis Test: Pirahã vs. The Global Matrix\n\n"
report += "The Pirahã are a hunter-gatherer tribe of the Amazon Basin, famous for having a language with no numbers, colors, or deep past/creation myths. This test pits their syntax against the entire global matrix to see if they possess any structural mythological crossover.\n\n"

report += "## Highest Syntactic Similarities\n"
for i, r in enumerate(results[:10]):
    report += f"### #{i+1}: PIRAHA <--> {r['target']} (Similarity: {r['similarity']:.2f}%)\n"

report += "\n## Lowest Syntactic Similarities (Absolute Repulsion)\n"
for i, r in enumerate(reversed(results[-10:])):
    report += f"### #{len(results)-i}: PIRAHA <--> {r['target']} (Similarity: {r['similarity']:.2f}%)\n"

with open("notebooks/piraha_test_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Report generated successfully.")
