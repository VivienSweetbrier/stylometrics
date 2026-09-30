import sqlite3
import pandas as pd
from pathlib import Path

try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
except ImportError:
    print("scikit-learn is not installed. Please run: pip install scikit-learn")
    exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

def run_local_lda():
    conn = sqlite3.connect(DB_PATH)
    
    # Fetch all words for our seeded pericopes (ignoring the unmapped 0 group)
    query = """
        SELECT v.pericope_id, w.lemma 
        FROM words w
        JOIN verses v ON w.verse_id = v.id
        WHERE v.pericope_id > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No mapped pericopes found.")
        return

    # Group words into "Documents" (where Document = 1 Pericope)
    print("Structuring pericopes into document blocks...")
    documents = df.groupby('pericope_id')['lemma'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    
    print(f"Loaded {len(documents)} pericopes for Latent Source detection.\n")

    # Create the Document-Term Matrix (Bag of Greek Words)
    vectorizer = CountVectorizer()
    dtm = vectorizer.fit_transform(documents['lemma'])
    feature_names = vectorizer.get_feature_names_out()

    # Run LDA (Variational Bayes algorithm - completely pre-compiled in C!)
    n_sources = 4  # Seeking Mark, Q, M, and L
    print(f"Running Latent Dirichlet Allocation (K={n_sources} Sources)...")
    lda = LatentDirichletAllocation(n_components=n_sources, random_state=42)
    lda.fit(dtm)

    output_file = BASE_DIR / "data" / "processed" / "lda_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== LATENT SOURCES DISCOVERED (Top 10 Greek Lemmas) ===\n")
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[:-10 - 1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            f.write(f"Source {topic_idx + 1}: {', '.join(top_words)}\n")

        f.write("\n=== PROBABILISTIC SOURCE MIXTURE PER PERICOPE ===\n")
        doc_topic_dist = lda.transform(dtm)
        for i, dist in enumerate(doc_topic_dist):
            pericope_id = documents['pericope_id'].iloc[i]
            primary_source = dist.argmax() + 1
            f.write(f"Pericope {pericope_id} draws heavily from Source {primary_source} (Probability: {dist.max()*100:.1f}%)\n")
            
    print(f"✅ LDA Analysis complete. Results saved to: {output_file}")

if __name__ == "__main__":
    run_local_lda()
