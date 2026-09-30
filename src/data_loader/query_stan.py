import sqlite3
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "stan_fatigue_data.json"

def needleman_wunsch(df_source, df_target):
    """
    Performs dynamic programming sequence alignment (Needleman-Wunsch) 
    between two text sequences to handle insertions, deletions, and mismatched lengths.
    """
    n, m = len(df_source), len(df_target)
    score = np.zeros((n + 1, m + 1))
    pointer = np.zeros((n + 1, m + 1), dtype=int)
    
    gap_penalty, match_score, mismatch_score = -1, 1, -1
    
    # Initialize boundaries
    for i in range(1, n + 1):
        score[i][0] = gap_penalty * i
        pointer[i][0] = 1 # up
    for j in range(1, m + 1):
        score[0][j] = gap_penalty * j
        pointer[0][j] = 2 # left
        
    # Fill matrix
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s_lemma = df_source.iloc[i-1]['lemma']
            t_lemma = df_target.iloc[j-1]['lemma']
            
            diag = score[i-1][j-1] + (match_score if s_lemma == t_lemma else mismatch_score)
            up = score[i-1][j] + gap_penalty
            left = score[i][j-1] + gap_penalty
            
            max_score = max(diag, up, left)
            score[i][j] = max_score
            
            if max_score == diag: pointer[i][j] = 0
            elif max_score == up: pointer[i][j] = 1
            else: pointer[i][j] = 2
                
    # Traceback
    align_src, align_tgt = [], []
    i, j = n, m
    while i > 0 or j > 0:
        if pointer[i][j] == 0:
            align_src.append(df_source.iloc[i-1])
            align_tgt.append(df_target.iloc[j-1])
            i, j = i - 1, j - 1
        elif pointer[i][j] == 1:
            align_src.append(df_source.iloc[i-1])
            align_tgt.append(None)
            i -= 1
        else:
            align_src.append(None)
            align_tgt.append(df_target.iloc[j-1])
            j -= 1
            
    return align_src[::-1], align_tgt[::-1]

def extract_aligned_stan_data(pericope_id: int):
    """
    Extracts text for MAT, MRK, LUK, performs robust sequence alignment, 
    and outputs multi-dimensional target arrays for Stan.
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT w.id, v.text_source, w.lemma, w.morph_tag, w.dependency_relation, v.position_index
        FROM words w
        JOIN verses v ON w.verse_id = v.id
        WHERE v.pericope_id = ?
        ORDER BY v.text_source, w.id
    """
    df = pd.read_sql_query(query, conn, params=(pericope_id,))
    conn.close()

    if df.empty:
        raise ValueError(f"No data found for pericope {pericope_id}")

    # For this model, we treat MAT as the hypothetical source (for Luke) to test Farrer
    df_mat = df[df['text_source'] == 'MAT'].reset_index(drop=True)
    df_luk = df[df['text_source'] == 'LUK'].reset_index(drop=True)
    
    if df_mat.empty or df_luk.empty:
        raise ValueError("Missing MAT or LUK data for this pericope.")

    print(f"Aligning Matthew (n={len(df_mat)}) and Luke (m={len(df_luk)})...")
    src_aligned, tgt_aligned = needleman_wunsch(df_mat, df_luk)
    
    # Initialize Multi-Dimensional Arrays
    Y_lexical, Y_morph, Y_syntax, text_position = [], [], [], []
    valid_count = 0

    for s_row, t_row in zip(src_aligned, tgt_aligned):
        if s_row is None or t_row is None:
            continue # Skip gaps for the fatigue index calculation
        
        # Multi-dimensional matching features
        Y_lexical.append(1 if s_row['lemma'] == t_row['lemma'] else 0)
        Y_morph.append(1 if s_row['morph_tag'] == t_row['morph_tag'] else 0)
        Y_syntax.append(1 if s_row['dependency_relation'] == t_row['dependency_relation'] else 0)
        
        valid_count += 1
        text_position.append(valid_count)

    # Normalize text position [0.0, 1.0] to test fatigue
    if valid_count > 1:
        text_position = [p / valid_count for p in text_position]

    stan_data = {
        "N": valid_count,
        "Y_lexical": Y_lexical,
        "Y_morph": Y_morph,
        "Y_syntax": Y_syntax,
        "text_position": text_position,
        "pericope": [pericope_id] * valid_count,
        "J": 1
    }

    return stan_data

if __name__ == "__main__":
    try:
        data = extract_aligned_stan_data(2) # Run on Pericope 2 (John the Baptist)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Success! Multi-dimensional Stan data exported to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")
