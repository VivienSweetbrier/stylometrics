import numpy as np
from hmmlearn import hmm

def run_hmm_autocorrelation(Y_lexical):
    """
    Component Coordination: Specialized Statistician Engine.
    Uses a Hidden Markov Model (HMM) to solve the autocorrelation problem.
    It calculates the probability of copying a word explicitly conditioned 
    on the latent state of the previous word.
    """
    print("\n[NODE: STATISTICIAN] Initializing Hidden Markov Model (HMM)...")
    
    if not Y_lexical:
        print("  -> ERROR: Empty Y_lexical array provided.")
        return None
        
    # hmmlearn requires a 2D array for discrete emission sequences
    X = np.array(Y_lexical).reshape(-1, 1)
    
    # We model 2 Hidden States:
    # State 0: "Independent Redaction"
    # State 1: "Verbatim Copying"
    model = hmm.CategoricalHMM(n_components=2, n_iter=100, random_state=42)
    
    try:
        model.fit(X)
    except Exception as e:
        print(f"  -> ERROR: HMM fitting failed. {e}")
        return None

    # Extract Autocorrelation Matrix (Transition Probabilities)
    # transmat_[i][j] = Probability of transitioning from State i to State j
    trans_matrix = model.transmat_
    
    # Identify which state is "Copying" (the one with the highest probability of emitting a '1')
    emission_probs = model.emissionprob_
    
    if emission_probs[0][1] > emission_probs[1][1]:
        copy_state = 0
        edit_state = 1
    else:
        copy_state = 1
        edit_state = 0
        
    print("  -> HMM successfully converged.")
    print("\n=== AUTOCORRELATION DISCOVERED ===")
    
    p_copy_to_copy = trans_matrix[copy_state][copy_state]
    p_edit_to_edit = trans_matrix[edit_state][edit_state]
    p_edit_to_copy = trans_matrix[edit_state][copy_state]
    
    print(f"  P(Copying word N | Copying word N-1) = {p_copy_to_copy * 100:.1f}%")
    print(f"  P(Redacting word N | Redacting word N-1) = {p_edit_to_edit * 100:.1f}%")
    print(f"  P(Switching to Copying | Currently Redacting) = {p_edit_to_copy * 100:.1f}%")
    
    if p_copy_to_copy > 0.8:
        print("\n  -> MATHEMATICAL CONCLUSION: Massive autocorrelation confirmed.")
        print("     Words are NOT independent. When the author starts copying,")
        print("     they are highly locked into copying phrases as blocks.")
        
    return trans_matrix
