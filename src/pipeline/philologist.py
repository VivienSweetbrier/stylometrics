import numpy as np

def align_with_transpositions(src_df, tgt_df):
    """
    Component Coordination: Specialized Philologist Engine.
    Executes a Needleman-Wunsch alignment upgraded with Damerau-Levenshtein 
    transposition logic to mathematically forgive Greek word-swapping.
    """
    src_lemmas = src_df['lemma'].tolist()
    tgt_lemmas = tgt_df['lemma'].tolist()
    n, m = len(src_lemmas), len(tgt_lemmas)
    
    score = np.zeros((n + 1, m + 1))
    pointer = np.zeros((n + 1, m + 1), dtype=int)
    # Pointers: 0=Diag, 1=Up(Gap), 2=Left(Gap), 3=Transposition
    
    # Statistical Weights
    MATCH = 2
    MISMATCH = -1
    GAP = -1
    SWAP = 3  # High reward for recognizing a stylistic transposition!
    
    # Initialize margins
    for i in range(1, n + 1):
        score[i, 0] = GAP * i
        pointer[i, 0] = 1
    for j in range(1, m + 1):
        score[0, j] = GAP * j
        pointer[0, j] = 2
        
    # Populate Dynamic Programming Matrix
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            is_match = src_lemmas[i-1] == tgt_lemmas[j-1]
            diag = score[i-1, j-1] + (MATCH if is_match else MISMATCH)
            up = score[i-1, j] + GAP
            left = score[i, j-1] + GAP
            
            options = [diag, up, left]
            
            # Check for Stylistic Transposition (Word Swapping)
            if i > 1 and j > 1 and src_lemmas[i-1] == tgt_lemmas[j-2] and src_lemmas[i-2] == tgt_lemmas[j-1]:
                options.append(score[i-2, j-2] + SWAP)
            else:
                options.append(-999999) # Impossible
                
            best = max(options)
            score[i, j] = best
            pointer[i, j] = options.index(best)
            
    # Traceback to generate the binary Y vector
    i, j = n, m
    Y_lexical = []
    
    while i > 0 or j > 0:
        p = pointer[i, j]
        if p == 0: # Diagonal
            Y_lexical.append(1 if src_lemmas[i-1] == tgt_lemmas[j-1] else 0)
            i -= 1
            j -= 1
        elif p == 1: # Up
            Y_lexical.append(0)
            i -= 1
        elif p == 2: # Left
            Y_lexical.append(0)
            j -= 1
        elif p == 3: # Transposition
            Y_lexical.extend([1, 1]) # Both swapped words count as matches!
            i -= 2
            j -= 2
            
    Y_lexical.reverse()
    
    # Calculate Quality Score
    matches = sum(Y_lexical)
    optimal = max(n, m)
    quality_score = matches / optimal if optimal > 0 else 0
    
    return min(1.0, quality_score), Y_lexical
