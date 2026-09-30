import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

def fetch_book_words(book_code):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT v.verse_ref, w.morph_tag 
        FROM words w
        JOIN verses v ON w.verse_id = v.id
        WHERE substr(v.verse_ref, 1, 3) = ? AND w.morph_tag IS NOT NULL
        ORDER BY v.id, w.id
    """
    df = pd.read_sql_query(query, conn, params=(book_code,))
    conn.close()
    return df

def get_cumulative_tags(tags, threshold=0.95):
    counts = Counter(tags)
    total = len(tags)
    cumulative = 0.0
    top_tags = []
    for tag, count in counts.most_common():
        top_tags.append(tag)
        cumulative += count / total
        if cumulative >= threshold:
            break
    return top_tags

def run_anomaly_node(book_code, window_size=250, step_size=100):
    print(f"\n=== GRAPH NODE: TEXTUAL CRITICISM (ANOMALY DETECTION) ===")
    print(f"  -> Scanning {book_code} for interpolations and scribal forgeries...")
    
    df = fetch_book_words(book_code)
    
    if df.empty:
        print("Error: Book not found.")
        return []
        
    global_len = len(df)
    if global_len == 0 or window_size <= 0:
        print("Error: Invalid lengths.")
        return []
        
    top_tags = get_cumulative_tags(df['morph_tag'], threshold=0.95)
    
    global_counts = Counter(df['morph_tag'])
    global_vec = np.array([global_counts[t] / global_len for t in top_tags]).reshape(1, -1)
    
    windows = []
    
    for i in range(0, max(1, len(df) - window_size + 1), step_size):
        window_df = df.iloc[i:i+window_size]
        if window_df.empty:
            continue
            
        start_verse = window_df.iloc[0]['verse_ref']
        end_verse = window_df.iloc[-1]['verse_ref']
        
        window_counts = Counter(window_df['morph_tag'])
        actual_window_size = len(window_df)
        window_vec = np.array([window_counts.get(t, 0) / actual_window_size for t in top_tags]).reshape(1, -1)
        
        sim = cosine_similarity(global_vec, window_vec)[0][0]
        distance = (1.0 - sim) * 100
        
        windows.append({
            'range': f"{start_verse} to {end_verse}",
            'distance': distance
        })

    windows.sort(key=lambda x: x['distance'], reverse=True)
    
    print(f"\n[TOP 3 HIGHEST STYLISTIC ANOMALIES IN {book_code}]")
    for i, w in enumerate(windows[:3]):
        print(f"  #{i+1}: {w['range']} (Anomaly Score: {w['distance']:.2f})")
    
    return windows

if __name__ == "__main__":
    run_anomaly_node("MRK")
    run_anomaly_node("JHN")
