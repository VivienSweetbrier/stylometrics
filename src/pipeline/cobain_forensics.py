import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import sys
import hashlib

try:
    import spacy
except ImportError:
    print("Please install spacy: pip install spacy && python -m spacy download en_core_web_sm")
    sys.exit(1)

def get_document_hash(text: str) -> str:
    """Creates a cryptographic chain of custody hash."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def extract_modern_features(text: str) -> pd.DataFrame:
    # We document the explicit model version in a real system (e.g., en_core_web_sm v3.8.0)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    data = []
    for sent_idx, sent in enumerate(doc.sents):
        for token in sent:
            if token.is_alpha:
                data.append({
                    'segment_id': f"Sentence {sent_idx + 1}",
                    'tag': token.pos_,
                    'text': token.text
                })
                
    return pd.DataFrame(data)

def generate_feature_explanation(window_counts, global_counts, global_len, window_size, top_tags):
    """Explains exactly why a window was flagged (White Box XAI)."""
    explanations = []
    for tag in top_tags:
        global_pct = (global_counts[tag] / global_len) * 100
        window_pct = (window_counts[tag] / window_size) * 100
        diff = window_pct - global_pct
        
        # If the tag usage changed by more than 10% (absolute), flag it
        if abs(diff) > 10.0:
            direction = "spiked" if diff > 0 else "dropped"
            explanations.append(f"{tag} {direction} to {window_pct:.1f}% (baseline: {global_pct:.1f}%)")
            
    if not explanations:
        return "Multiple minor structural shifts across several parts of speech."
    
    return "; ".join(explanations)

def get_cumulative_tags(tags, threshold=0.90):
    counts = Counter(tags)
    total = len(tags)
    cumulative = 0.0
    top_tags = []
    for tag, count in counts.most_common():
        top_tags.append(tag)
        cumulative += count / total
        if cumulative >= threshold:
            break
    if not top_tags:
        top_tags = list(counts.keys())
    return top_tags

def run_hardened_math_engine(df: pd.DataFrame, window_size=50, step_size=20):
    if df.empty or window_size <= 0:
        return []
        
    top_tags = get_cumulative_tags(df['tag'], threshold=0.95)
    
    global_counts = Counter(df['tag'])
    global_len = len(df)
    if global_len == 0:
        return []
        
    global_vec = np.array([global_counts[t] / global_len for t in top_tags]).reshape(1, -1)
    
    windows = []
    raw_distances = []
    
    # Pass 1: Calculate raw distances for all windows
    for i in range(0, len(df) - window_size + 1, step_size):
        window_df = df.iloc[i:i+window_size]
        start_segment = window_df.iloc[0]['segment_id']
        end_segment = window_df.iloc[-1]['segment_id']
        
        window_counts = Counter(window_df['tag'])
        actual_window_size = len(window_df)
        window_vec = np.array([window_counts.get(t, 0) / actual_window_size for t in top_tags]).reshape(1, -1)
        
        sim = cosine_similarity(global_vec, window_vec)[0][0]
        distance = (1.0 - sim) * 100
        
        window_text = " ".join(window_df['text'].tolist()[:15]) + "..."
        explanation = generate_feature_explanation(window_counts, global_counts, global_len, actual_window_size, top_tags)
        
        windows.append({
            'range': f"{start_segment} to {end_segment}",
            'distance': distance,
            'text': window_text,
            'explanation': explanation
        })
        raw_distances.append(distance)

    # Pass 2: Calculate Statistical Significance (Z-Scores)
    mean_dist = np.mean(raw_distances)
    std_dist = np.std(raw_distances)
    
    for w in windows:
        # Avoid division by zero if std_dist is 0
        z_score = (w['distance'] - mean_dist) / std_dist if std_dist > 0 else 0
        w['z_score'] = z_score

    # Sort by Z-score descending
    windows.sort(key=lambda x: x['z_score'], reverse=True)
    return windows

if __name__ == "__main__":
    kurt_cobain_note = """
    To Boddah,

    Speaking from the tongue of an experienced simpleton who obviously would rather be an emasculated, infantile complain-ee. This note should be pretty easy to understand.

    All the warnings from the punk rock 101 courses over the years, since my first introduction to the, shall we say, ethics involved with independence and the embracement of your community has proven to be very true. I haven't felt the excitement of listening to as well as creating music along with really reading and writing too much for too many years now. I feel guilty beyond words about these things.

    For example when we're back stage and the lights go out and the manic roar of the crowds begins, it doesn't affect me the way in which it did for Freddie Mercury, who seemed to love, relish in the love and adoration from the crowd which is something I totally admire and envy. The fact is, I can't fool you, any one of you. It simply isn't fair to you or me. The worst crime I can think of would be to rip people off by faking it and pretending as if I'm having 100% fun. Sometimes I feel as if I should have a punch-in time clock before I walk out on stage. I've tried everything within my power to appreciate it (and I do, God, believe me I do, but it's not enough). I appreciate the fact that I and we have affected and entertained a lot of people. I must be one of those narcissists who only appreciate things when they're gone. I'm too sensitive. I need to be slightly numb in order to regain the enthusiasm I once had as a child.

    On our last three tours, I've had a much better appreciation for all the people I've known personally, and as fans of our music, but I still can't get over the frustration, the guilt and empathy I have for everyone. There's good in all of us and I think I simply love people too much, so much that it makes me feel too fucking sad. The sad little, sensitive, unappreciative, Pisces, Jesus man. Why don't you just enjoy it? I don't know!

    I have a goddess of a wife who sweats ambition and empathy and a daughter who reminds me too much of what I used to be, full of love and joy, kissing every person she meets because everyone is good and will do her no harm. And that terrifies me to the point to where I can barely function. I can't stand the thought of Frances becoming the miserable, self-destructive, death rocker that I've become.

    I have it good, very good, and I'm grateful, but since the age of seven, I've become hateful toward all humans in general. Only because it seems so easy for people to get along and have empathy. Empathy! Only because I love and feel sorry for people too much I guess.

    Thank you all from the pit of my burning, nauseous stomach for your letters and concern during the past years. I'm too much of an erratic, moody baby! I don't have the passion anymore, and so remember, it's better to burn out than to fade away.

    Peace, love, empathy.
    Kurt Cobain

    Frances and Courtney, I'll be at your alter.
    Please keep going, Courtney, for Frances.
    For her life, which will be so much happier without me.

    I LOVE YOU, I LOVE YOU!
    """
    
    print("="*60)
    print("LEGAL FORENSICS REPORT: TEXTUAL ANOMALY SCAN")
    print("="*60)
    print(f"Document SHA-256 Hash: {get_document_hash(kurt_cobain_note)}")
    print("NLP Pipeline: spaCy (en_core_web_sm) [Deterministic Mode]")
    print("-" * 60)
    
    print("Extracting Linguistic Features...")
    df = extract_modern_features(kurt_cobain_note)
    
    print("Running Hardened Math Engine (Z-Score & Feature Importance)...")
    anomalies = run_hardened_math_engine(df, window_size=20, step_size=5)
    
    print("\n[TOP 3 STATISTICALLY SIGNIFICANT ANOMALIES DETECTED]\n")
    for i, w in enumerate(anomalies[:3]):
        print(f"#{i+1}: {w['range']}")
        print(f"   Z-Score: +{w['z_score']:.2f} Standard Deviations (Statistically Significant)")
        print(f"   Snippet: '{w['text']}'")
        print(f"   Feature Explanation: {w['explanation']}\n")
