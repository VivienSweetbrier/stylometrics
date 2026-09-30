import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

def fetch_chunked_morphology(chunk_size=1000, db_path=None):
    if db_path is None:
        db_path = DB_PATH
        
    print(f"Loading morphology from {db_path}...")
    conn = sqlite3.connect(db_path)
    
    if 'catss' in str(db_path):
        query = """
            SELECT b.osis as book, m.parse_code as morph_tag 
            FROM lxx_morph m
            JOIN verses v ON m.verse_id = v.id
            JOIN books b ON v.book_id = b.id
            WHERE m.parse_code IS NOT NULL
            ORDER BY b.osis, v.id, m.position
        """
    elif 'hebrew' in str(db_path):
        query = """
            SELECT 
                CASE substr("xml:id", 1, 3)
                    WHEN 'n01' THEN 'Gen' WHEN 'n02' THEN 'Exod' WHEN 'n03' THEN 'Lev'
                    WHEN 'n04' THEN 'Num' WHEN 'n05' THEN 'Deut' WHEN 'n06' THEN 'Josh'
                    WHEN 'n07' THEN 'Judg' WHEN 'n08' THEN 'Ruth' WHEN 'n09' THEN '1Sam'
                    WHEN 'n10' THEN '2Sam' WHEN 'n11' THEN '1Kgs' WHEN 'n12' THEN '2Kgs'
                    WHEN 'n13' THEN '1Chr' WHEN 'n14' THEN '2Chr' WHEN 'n15' THEN 'Ezra'
                    WHEN 'n16' THEN 'Neh' WHEN 'n17' THEN 'Esth' WHEN 'n18' THEN 'Job'
                    WHEN 'n19' THEN 'Ps' WHEN 'n20' THEN 'Prov' WHEN 'n21' THEN 'Eccl'
                    WHEN 'n22' THEN 'Song' WHEN 'n23' THEN 'Isa' WHEN 'n24' THEN 'Jer'
                    WHEN 'n25' THEN 'Lam' WHEN 'n26' THEN 'Ezek' WHEN 'n27' THEN 'Dan'
                    WHEN 'n28' THEN 'Hos' WHEN 'n29' THEN 'Joel' WHEN 'n30' THEN 'Amos'
                    WHEN 'n31' THEN 'Obad' WHEN 'n32' THEN 'Jonah' WHEN 'n33' THEN 'Mic'
                    WHEN 'n34' THEN 'Nah' WHEN 'n35' THEN 'Hab' WHEN 'n36' THEN 'Zeph'
                    WHEN 'n37' THEN 'Hag' WHEN 'n38' THEN 'Zech' WHEN 'n39' THEN 'Mal'
                    ELSE 'UNK' END as book, 
                morph as morph_tag 
            FROM words 
            WHERE morph IS NOT NULL
            ORDER BY substr("xml:id", 1, 3), "xml:id"
        """
    else:
        # Check if the legacy 'verses' table exists (for synoptics.db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verses'")
        has_verses = cursor.fetchone() is not None
        
        if has_verses:
            query = """
                SELECT substr(v.verse_ref, 1, 3) as book, w.morph_tag 
                FROM words w
                JOIN verses v ON w.verse_id = v.id
                WHERE w.morph_tag IS NOT NULL
                ORDER BY substr(v.verse_ref, 1, 3), v.id, w.id
            """
        else:
            # Fallback to the unified CorpusIngestionEngine schema
            query = """
                SELECT text_source as book, pos as morph_tag
                FROM words
                WHERE pos IS NOT NULL AND pos != 'U'
                ORDER BY text_source, id
            """
        
    chunks = []
    labels = []
    books = []
    
    current_book = None
    current_chunk = []
    
    for df_chunk in pd.read_sql_query(query, conn, chunksize=50000):
        for _, row in df_chunk.iterrows():
            book = row['book']
            tag = row['morph_tag']
            
            if current_book is None:
                current_book = book
                
            if book != current_book:
                if len(current_chunk) >= (chunk_size * 0.8): 
                    chunks.append(current_chunk)
                    labels.append(f"{current_book}_{len(chunks)}")
                    books.append(current_book)
                current_book = book
                current_chunk = []
                
            current_chunk.append(tag)
            
            if len(current_chunk) == chunk_size:
                chunks.append(current_chunk)
                labels.append(f"{current_book}_{len(chunks)}")
                books.append(current_book)
                current_chunk = []

    if current_chunk and len(current_chunk) >= (chunk_size * 0.8):
        chunks.append(current_chunk)
        labels.append(f"{current_book}_{len(chunks)}")
        books.append(current_book)
                
    conn.close()
    return chunks, labels, books

def _get_top_tags(chunks, cumulative_threshold=0.90):
    all_tags = [tag for chunk in chunks for tag in chunk]
    tag_counts = Counter(all_tags)
    total_tags = len(all_tags)
    
    top_tags = []
    cumulative = 0.0
    for tag, count in tag_counts.most_common():
        top_tags.append(tag)
        cumulative += count / total_tags
        if cumulative >= cumulative_threshold:
            break
            
    return top_tags

def run_burrows_delta():
    print("\n=== GRAPH NODE: STYLOMETRIST (BURROWS' DELTA) ===")
    chunks, labels, books = fetch_chunked_morphology(chunk_size=1000)
    
    if not chunks:
        print("Error: No data retrieved.")
        return

    print("  -> Extracting grammatical fingerprints (90% cumulative mass)...")
    top_tags = _get_top_tags(chunks, cumulative_threshold=0.90)
    
    freq_matrix = np.zeros((len(chunks), len(top_tags)))
    for i, chunk in enumerate(chunks):
        chunk_counter = Counter(chunk)
        chunk_len = len(chunk)
        for j, tag in enumerate(top_tags):
            freq_matrix[i, j] = chunk_counter[tag] / chunk_len if chunk_len > 0 else 0
            
    print("  -> Applying Z-score normalization...")
    means = np.mean(freq_matrix, axis=0)
    stds = np.std(freq_matrix, axis=0)
    
    stds[stds == 0] = np.finfo(float).eps 
    z_scores = (freq_matrix - means) / stds
    
    print("  -> Applying Principal Component Analysis (PCA) to Z-scores...")
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(z_scores)
    
    unique_books = list(set(books))
    book_z_vectors = {}
    
    for b in unique_books:
        indices = [i for i, book in enumerate(books) if book == b]
        book_z_vectors[b] = np.mean(z_scores[indices], axis=0)
        
    def get_similarity(b1, b2):
        if b1 in book_z_vectors and b2 in book_z_vectors:
            vec1 = book_z_vectors[b1].reshape(1, -1)
            vec2 = book_z_vectors[b2].reshape(1, -1)
            sim = cosine_similarity(vec1, vec2)[0][0]
            return ((sim + 1) / 2) * 100
        return None

    print("\n=== PAULINE AUTHORSHIP ATTRIBUTION (BASELINE: ROMANS) ===")
    
    pauline_epistles = ['1CO', '2CO', 'GAL', 'PHP', '1TH', 'PHM']
    deutero_paulines = ['EPH', 'COL', '2TH']
    pastorals = ['1TI', '2TI', 'TIT']
    hebrews = ['HEB']
    
    def print_category(category_name, books_list):
        print(f"\n[{category_name}]")
        for book in books_list:
            sim = get_similarity("ROM", book)
            if sim is not None:
                print(f"Romans vs {book}: {sim:.1f}%")
            else:
                print(f"Romans vs {book}: Not enough chunk data (book too short)")

    print_category("UNDISPUTED EPISTLES (Control Group)", pauline_epistles)
    print_category("DEUTERO-PAULINE (Disputed)", deutero_paulines)
    print_category("PASTORAL EPISTLES (Likely Forgeries)", pastorals)
    print_category("HEBREWS", hebrews)

    print("\n=== STYLOMETRIC CONCLUSION ===")
    print("  -> Watch the similarity percentages drop as we move from undisputed texts into the pseudepigrapha.")

if __name__ == "__main__":
    run_burrows_delta()

def compare_books(baseline, targets, chunk_size=1000, db_path=None):
    """API endpoint for the Streamlit Web App."""
    chunks, labels, books = fetch_chunked_morphology(chunk_size, db_path)
    if not chunks:
        return {}
        
    top_tags = _get_top_tags(chunks, cumulative_threshold=0.90)
    
    freq_matrix = np.zeros((len(chunks), len(top_tags)))
    for i, chunk in enumerate(chunks):
        chunk_counter = Counter(chunk)
        chunk_len = len(chunk)
        for j, tag in enumerate(top_tags):
            freq_matrix[i, j] = chunk_counter[tag] / chunk_len if chunk_len > 0 else 0
            
    means = np.mean(freq_matrix, axis=0)
    stds = np.std(freq_matrix, axis=0)
    stds[stds == 0] = np.finfo(float).eps 
    z_scores = (freq_matrix - means) / stds
    
    unique_books = list(set(books))
    book_z_vectors = {}
    for b in unique_books:
        indices = [i for i, book in enumerate(books) if book == b]
        book_z_vectors[b] = np.mean(z_scores[indices], axis=0)
        
    results = {}
    if baseline not in book_z_vectors:
        return results
        
    vec_base = book_z_vectors[baseline].reshape(1, -1)
    for t in targets:
        if t in book_z_vectors:
            vec_t = book_z_vectors[t].reshape(1, -1)
            sim = cosine_similarity(vec_base, vec_t)[0][0]
            results[t] = ((sim + 1) / 2) * 100
    return results

