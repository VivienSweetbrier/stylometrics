import sqlite3
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from pathlib import Path
import os

def generate_homeric_ngrams(db_path: str, n=3):
    """
    Extracts ordered lemmas from the database and generates N-Grams
    to represent Homeric formulaic blocks (e.g. 'swift footed Achilles').
    """
    conn = sqlite3.connect(db_path)
    
    # Check if this is the flattened schema (has 'text_source' and 'pos') or legacy schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(words)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'text_source' in columns and 'lemma' in columns:
        # Flattened schema
        query = """
            SELECT 
                text_source AS book,
                lemma
            FROM words
            WHERE lemma IS NOT NULL AND lemma != ''
            ORDER BY id
        """
    else:
        # Legacy Homeric schema
        query = """
            SELECT 
                p.tradition_type AS book,
                w.lemma
            FROM words w
            JOIN verses v ON w.verse_id = v.id
            JOIN pericopes p ON v.pericope_id = p.id
            WHERE w.lemma IS NOT NULL AND w.lemma != ''
            ORDER BY p.id, v.position_index, w.id
        """
        
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return None

    # Group by book and create space-separated strings of lemmas
    book_texts = df.groupby('book')['lemma'].apply(lambda x: ' '.join(x)).reset_index()
    return book_texts

def run_bard_clustering(db_path: str, n_bards=4):
    """
    Executes the Source Modeler Node:
    Uses LDA on formulaic N-Grams to cluster Books into latent 'Bards'.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    print("Extracting sequential lemma blocks from the corpus...")
    book_texts = generate_homeric_ngrams(db_path, n=3)
    
    if book_texts is None:
        print("Database is empty.")
        return

    # 1. HMM-Gating Simulation (Filter for Formulaic Blocks)
    # We use a CountVectorizer configured for N-Grams (3-grams).
    # min_df=2 ensures we ONLY look at repeated formulaic blocks (gating out random hapax legomena).
    print("Vectorizing repeated Homeric formulas (N-Grams)...")
    vectorizer = CountVectorizer(ngram_range=(3, 3), min_df=2)
    
    try:
        dtm = vectorizer.fit_transform(book_texts['lemma'])
    except ValueError:
        print("Not enough repeated N-grams found to cluster.")
        return

    # 2. Latent Dirichlet Allocation (The Source Modeler)
    print(f"Executing Markov-Topic LDA Clustering (K={n_bards} Bards)...")
    lda = LatentDirichletAllocation(n_components=n_bards, random_state=42, max_iter=20)
    lda_output = lda.fit_transform(dtm)

    # 3. Assign each Book to its dominant 'Bard'
    dominant_bard = np.argmax(lda_output, axis=1)
    book_texts['Assigned_Bard'] = [f"Bard_{b+1}" for b in dominant_bard]
    book_texts['Confidence'] = np.max(lda_output, axis=1)

    # 4. Generate the Markdown Report
    res_df = book_texts[['book', 'Assigned_Bard', 'Confidence']].sort_values(by=['Assigned_Bard', 'Confidence'], ascending=[True, False])
    
    report_path = Path(db_path).parent.parent.parent / "notebooks" / "bard_clustering_report.md"
    os.makedirs(report_path.parent, exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write("# Forensic Antiquity Engine: Homeric Bard Clustering\n\n")
        f.write("This report utilizes a Markov-Topic Model (LDA applied to 3-gram lemma blocks) to isolate distinct latent sources ('Bards') across the Homeric epics.\n\n")
        
        for bard in res_df['Assigned_Bard'].unique():
            f.write(f"## {bard} (Latent Source)\n")
            bard_books = res_df[res_df['Assigned_Bard'] == bard]
            for _, row in bard_books.iterrows():
                f.write(f"- **{row['book']}** (Confidence: {row['Confidence'] * 100:.2f}%)\n")
            f.write("\n")
            
    print(f"Success! Bard Clustering complete. Report generated at: {report_path}")
    return res_df

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "processed" / "homer.db"
    
    # We hypothesize 3 to 4 dominant oral traditions (e.g., Core Aeolic, Ionian Expansion, Monumental Composer, etc.)
    run_bard_clustering(str(db_path), n_bards=3)
