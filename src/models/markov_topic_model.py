import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from hmmlearn import hmm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Import our specialized Graph Node
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "pipeline"))
from philologist import align_with_transpositions

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

def fetch_pericopes():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT v.pericope_id, v.text_source, w.lemma 
        FROM words w
        JOIN verses v ON w.verse_id = v.id
        WHERE v.pericope_id > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def extract_copied_blocks():
    """
    Step 1: The HMM Gate. 
    Uses the Philologist and Statistician nodes to strip away independent 
    author redaction, returning ONLY the heavily copied text sequences.
    """
    df = fetch_pericopes()
    pericope_ids = df['pericope_id'].unique()
    
    gated_documents = []
    doc_labels = []
    
    for p_id in sorted(pericope_ids):
        p_df = df[df['pericope_id'] == p_id]
        mat_df = p_df[p_df['text_source'] == 'MAT'].reset_index(drop=True)
        luk_df = p_df[p_df['text_source'] == 'LUK'].reset_index(drop=True)
        
        # If we lack a pair to compare, treat as unique source material (e.g. L or M)
        if mat_df.empty or luk_df.empty:
            lemmas = p_df['lemma'].dropna().tolist()
            gated_documents.append(' '.join(lemmas))
            doc_labels.append(p_id)
            continue
            
        # 1A. Run Philologist (Alignment)
        score, Y_lexical = align_with_transpositions(mat_df, luk_df)
        
        # 1B. Run Statistician (HMM Gate)
        if len(Y_lexical) > 5:
            X = np.array(Y_lexical).reshape(-1, 1)
            model = hmm.CategoricalHMM(n_components=2, n_iter=10, random_state=42)
            model.fit(X)
            hidden_states = model.predict(X)
            
            # Identify which state mathematically represents "Copying"
            state_means = [np.mean(np.array(Y_lexical)[hidden_states == i]) for i in range(2)]
            copy_state = np.argmax(state_means)
            
            # GATE THE TEXT: Only keep lemmas where the author was in the "Copying" state!
            gated_lemmas = []
            for i, state in enumerate(hidden_states):
                if state == copy_state and i < len(luk_df):
                    gated_lemmas.append(luk_df['lemma'].iloc[i])
                    
            gated_documents.append(' '.join(gated_lemmas))
            doc_labels.append(p_id)
        else:
            gated_documents.append(' '.join(luk_df['lemma'].dropna().tolist()))
            doc_labels.append(p_id)
            
    return gated_documents, doc_labels

def run_markov_topic_model():
    print("=== GRAPH NODE: MARKOV-TOPIC MODEL ===")
    
    # 1. HMM Gate
    print("  -> Gating text through Hidden Markov Model to remove independent redaction...")
    documents, labels = extract_copied_blocks()
    
    # 2. N-Gram Vectorization (Sequence Enforcer)
    print("  -> Vectorizing surviving text into sequential N-Grams (Tri-grams to Pent-grams)...")
    # ngram_range=(2,4) forces the LDA to cluster exact phrases, completely solving the Bag-of-Words flaw
    vectorizer = CountVectorizer(ngram_range=(2, 4), min_df=1) 
    
    try:
        dtm = vectorizer.fit_transform(documents)
    except ValueError:
        print("  -> ERROR: Not enough sequential data to form N-Grams.")
        return
        
    feature_names = vectorizer.get_feature_names_out()
    
    # 3. Latent Dirichlet Allocation
    n_sources = 3 # Stress Test: Testing 3 latent sources to see if John is mathematically unique
    print(f"  -> Running LDA to cluster sequences into Latent Sources...")
    lda = LatentDirichletAllocation(n_components=n_sources, random_state=42)
    lda.fit(dtm)
    
    output_file = BASE_DIR / "data" / "processed" / "markov_topic_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n=== MARKOV-TOPIC SOURCES DISCOVERED (Top Sequence Blocks) ===\n")
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[:-5 - 1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            f.write(f"\nLatent Source {topic_idx + 1} Identifiers:\n")
            for phrase in top_words:
                f.write(f"  - '{phrase}'\n")

        f.write("\n=== PROBABILISTIC SOURCE ASSIGNMENTS ===\n")
        doc_topic_dist = lda.transform(dtm)
        for i, dist in enumerate(doc_topic_dist):
            primary_source = dist.argmax() + 1
            f.write(f"Pericope {labels[i]} -> Bound to Source {primary_source} (Sequence Match Prob: {dist.max()*100:.1f}%)\n")
            
    print(f"  -> SUCCESS! Results saved to {output_file} to avoid Unicode console errors.")

if __name__ == "__main__":
    run_markov_topic_model()
