import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter

db_dir = Path("data/processed")
isolates = ['san.db', 'andamanese.db', 'ainu.db']

def get_isolated_lemmas(db_path):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT lemma FROM words WHERE pos = 'ISOLATED_MORPHOLOGY' AND lemma IS NOT NULL", conn)
        conn.close()
        return df['lemma'].tolist()
    except Exception as e:
        return []

all_lemmas = {}
for db in isolates:
    path = db_dir / db
    if path.exists():
        lemmas = get_isolated_lemmas(path)
        all_lemmas[db] = Counter(lemmas).most_common(10)

report = "# Deep Dive: ISOLATED_MORPHOLOGY Tokens\n\n"
report += "Extracting the actual raw lemma tokens that the NLP engine flagged as `ISOLATED_MORPHOLOGY` to decipher the grammatical black box.\n\n"

for db, top_lemmas in all_lemmas.items():
    report += f"## {db.upper()}\n"
    for lemma, count in top_lemmas:
        report += f"- `{lemma}` (Occurrences: {count})\n"
    report += "\n"

with open("notebooks/isolated_morphology_deepdive.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Done")
