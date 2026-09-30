import sqlite3
import pandas as pd
import json
import re
from pathlib import Path
import os

def extract_fatigue_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "processed" / "homer.db"
    report_path = base_dir / "notebooks" / "bard_clustering_report.md"
    
    # 1. Read the DAG output from the Source Modeler (Bard Assignments)
    bard_map = {}
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            current_bard = None
            for line in f:
                if line.startswith("## Bard_"):
                    current_bard = line.split()[1]
                elif line.startswith("- **"):
                    book = line.split("**")[1]
                    bard_map[book] = current_bard
    
    if not bard_map:
        print("Error: Could not find Bard assignments. Run Source Modeler first.")
        return

    # 2. Extract Sequential Data from SQLite
    conn = sqlite3.connect(db_path)
    query = """
        SELECT 
            p.tradition_type AS book,
            v.position_index,
            w.lemma
        FROM words w
        JOIN verses v ON w.verse_id = v.id
        JOIN pericopes p ON v.pericope_id = p.id
        WHERE w.lemma IS NOT NULL AND w.lemma != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # 3. Define the Dependent Variable (Y_formulaic)
    # We define 'formulaic crutches' as the top 200 most frequently repeated lemmas in the corpus.
    # We want to test if the Bard relies on these stock formulas MORE as they get tired (position_index increases).
    top_lemmas = df['lemma'].value_counts().nlargest(200).index
    df['Y_formulaic'] = df['lemma'].isin(top_lemmas).astype(int)

    # 4. Map the Bards
    df['Bard_ID'] = df['book'].map(bard_map)

    # 5. Isolate Bard_1 for the Bayesian Pilot Test (to ensure fast MCMC sampling)
    # Testing fatigue strictly within the "Archaic Battle Tradition"
    df_bard1 = df[df['Bard_ID'] == 'Bard_1'].copy()
    
    # Sort by text position
    df_bard1 = df_bard1.sort_values(by=['book', 'position_index'])

    # Sample data to ensure rstanarm doesn't hang (MCMC on 100,000 rows takes hours)
    # We take a representative sequence of 2,000 words.
    df_sample = df_bard1.sample(n=2000, random_state=42).sort_values(by='position_index')

    # 6. Export to JSON for R/Stan
    output_data = {
        "Y_formulaic": df_sample['Y_formulaic'].tolist(),
        "position_index": df_sample['position_index'].tolist(),
        "book": df_sample['book'].tolist()
    }
    
    out_path = base_dir / "data" / "processed" / "stan_homer_fatigue.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f)
        
    print(f"Success! Extracted {len(df_sample)} sequential data points for Bard_1.")
    print(f"Data saved to {out_path} for Bayesian Inference.")

if __name__ == "__main__":
    extract_fatigue_data()
