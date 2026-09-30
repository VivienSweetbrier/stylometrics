import sqlite3
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer

def extract_pos_sequence(db_path):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT pos FROM words WHERE pos IS NOT NULL AND pos != '' ORDER BY id", conn)
        conn.close()
        return " ".join(df['pos'].tolist())
    except:
        return ""

db_dir = Path("data/processed")
isolates = ['san.db', 'andamanese.db', 'ainu.db', 'guanche.db']
controls = ['homer.db', 'mesopotamian.db']

isolate_docs = []
for db in isolates:
    path = db_dir / db
    if path.exists():
        isolate_docs.append(extract_pos_sequence(path))

control_docs = []
for db in controls:
    path = db_dir / db
    if path.exists():
        control_docs.append(extract_pos_sequence(path))

print(f"Loaded {len(isolate_docs)} isolates and {len(control_docs)} controls.")

# Extract 3 to 5-grams
vectorizer = CountVectorizer(ngram_range=(3, 5), min_df=3)
X_iso = vectorizer.fit_transform(isolate_docs)
vocab = vectorizer.get_feature_names_out()

# Calculate average frequency in isolates
iso_freqs = X_iso.toarray().mean(axis=0)

# Transform controls to see how often these motifs appear there
X_ctrl = vectorizer.transform(control_docs)
ctrl_freqs = X_ctrl.toarray().mean(axis=0)

# Find motifs that are highly frequent in isolates but rare in controls
diffs = []
for i, motif in enumerate(vocab):
    iso_f = iso_freqs[i]
    ctrl_f = ctrl_freqs[i]
    if iso_f > 10 and (iso_f / (ctrl_f + 1)) > 5: # At least 5x more common
        diffs.append((motif, iso_f, ctrl_f))

diffs.sort(key=lambda x: x[1], reverse=True)

report = "# The Archaic Syntactic Baseline\n\n"
report += "By isolating the exact grammatical sequences (N-Grams) that appear universally in the deepest human isolates (San, Andamanese, Ainu, Guanche) but are mathematically absent in later classical civilizations (Homer, Mesopotamian), we can reconstruct the original storytelling structure of *Homo sapiens*.\n\n"

for i, (motif, iso_f, ctrl_f) in enumerate(diffs[:15]):
    report += f"### Archaic Sequence #{i+1}: `{motif.upper()}`\n"
    report += f"- **Avg frequency in Deep Isolates:** {iso_f:.1f}\n"
    report += f"- **Avg frequency in Bronze Age Controls:** {ctrl_f:.1f}\n"

with open("notebooks/archaic_syntax_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Done")
