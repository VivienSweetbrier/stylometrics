import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
try:
    import spacy
except ImportError:
    print("Please install spacy: pip install spacy && python -m spacy download en_core_web_sm")
    exit()

def extract_modern_features(text: str) -> pd.DataFrame:
    """
    Ingests raw English text and outputs a DataFrame identical in structure 
    to what the Antiquity Engine expects (replacing verses with sentences 
    and Greek morphology with English POS tags).
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    data = []
    for sent_idx, sent in enumerate(doc.sents):
        for token in sent:
            if token.is_alpha:  # Ignore punctuation/spaces
                data.append({
                    'segment_id': f"Sentence {sent_idx + 1}",
                    'tag': token.pos_  # Part of Speech tag (e.g., NOUN, VERB)
                })
                
    return pd.DataFrame(data)

def run_math_engine(df: pd.DataFrame, window_size=50, step_size=20):
    """
    The exact same mathematical core from your anomaly_node.py,
    just decoupled from the SQLite database.
    """
    if df.empty:
        return []
        
    # Baseline: Top 15 POS Tags in the text
    top_tags = [tag for tag, count in Counter(df['tag']).most_common(15)]
    
    # Global Baseline Vector
    global_counts = Counter(df['tag'])
    global_len = len(df)
    global_vec = np.array([global_counts[t] / global_len for t in top_tags]).reshape(1, -1)
    
    windows = []
    
    for i in range(0, len(df) - window_size + 1, step_size):
        window_df = df.iloc[i:i+window_size]
        start_segment = window_df.iloc[0]['segment_id']
        end_segment = window_df.iloc[-1]['segment_id']
        
        window_counts = Counter(window_df['tag'])
        window_vec = np.array([window_counts[t] / window_size for t in top_tags]).reshape(1, -1)
        
        sim = cosine_similarity(global_vec, window_vec)[0][0]
        distance = (1.0 - sim) * 100
        
        windows.append({
            'range': f"{start_segment} to {end_segment}",
            'distance': distance
        })

    windows.sort(key=lambda x: x['distance'], reverse=True)
    return windows

if __name__ == "__main__":
    # Simulated Confession Document
    # First half is written naturally by a suspect (colloquial, simple verbs).
    # Second half (the actual confession) is written by a police officer (formal, procedural nouns/verbs).
    
    sample_text = """
    I was just hanging out at the gas station around 10 PM. I bought a soda and some chips. 
    I saw a guy walk in but I didn't think much of it. I was just minding my own business. 
    My friend picked me up a few minutes later and we went to his house to play video games.
    I do not know anything about a robbery. 
    
    I now wish to formally confess to the aforementioned robbery of the retail establishment. 
    I obtained unlawful entry through the rear access point. I forcibly extracted the currency 
    from the cash receptacle. I executed this criminal act with full malice aforethought and 
    acknowledge my culpability in this illicit enterprise.
    """
    
    print("Processing text via spaCy NLP...")
    df = extract_modern_features(sample_text)
    
    print("Running Anomaly Math Engine...")
    anomalies = run_math_engine(df, window_size=20, step_size=5)
    
    print("\n[TOP 3 HIGHEST STYLISTIC ANOMALIES DETECTED]")
    for i, w in enumerate(anomalies[:3]):
        print(f"  #{i+1}: {w['range']} (Anomaly Score: {w['distance']:.2f})")
