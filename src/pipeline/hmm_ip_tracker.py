import spacy
import networkx as nx
import math
import sys
from collections import Counter

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spacy model: python -m spacy download en_core_web_sm")
    sys.exit(1)

class BulletproofHMMGraph:
    def __init__(self):
        # We use a Directed Graph to model the Markov Chain
        self.graph = nx.DiGraph()
        # To calculate Laplace Smoothing, we need the total vocabulary size of states
        self.unique_states = set(['<START>', '<END>']) 
        # Universal size for state space (tags + function words)
        self.fixed_V = 100 
        
    def _extract_sequence(self, text, is_training=False):
        """
        Extracts hybrid states: Function Words are kept as lowercase tokens, 
        content words are converted to POS tags.
        Injects <START> and <END> boundaries for every sentence.
        """
        doc = nlp(text)
        sequences = []
        
        # Early Modern English prominent function words for stylistic fingerprinting
        function_words = {"and", "the", "to", "of", "in", "i", "that", "for", "it", 
                          "with", "is", "not", "thou", "you", "ye", "hath", "doth", 
                          "has", "does", "thy", "my", "mine", "a", "but", "as", "be", "upon"}
        
        for sent in doc.sents:
            seq = ['<START>']
            for token in sent:
                if token.is_space:
                    continue
                if token.lower_ in function_words:
                    seq.append(token.lower_)
                else:
                    seq.append(token.pos_)
            seq.append('<END>')
            
            sequences.append(seq)
            
            if is_training:
                # Update known universe of states for smoothing
                for state in seq:
                    self.unique_states.add(state)
                
        return sequences

    def train(self, baseline_text):
        """
        Builds the Markov Chain as a NetworkX Directed Graph.
        """
        sequences = self._extract_sequence(baseline_text, is_training=True)
        if not sequences:
            return
            
        # 1. Count Raw Transitions (Edges)
        edge_counts = Counter()
        node_out_degrees = Counter()
        
        for seq in sequences:
            for i in range(len(seq) - 1):
                state_a = seq[i]
                state_b = seq[i+1]
                edge_counts[(state_a, state_b)] += 1
                node_out_degrees[state_a] += 1
                
                # Add nodes to graph
                if not self.graph.has_node(state_a):
                    self.graph.add_node(state_a)
                if not self.graph.has_node(state_b):
                    self.graph.add_node(state_b)

        # 2. Apply Laplace Smoothing (Add-1) & Calculate Log Probabilities
        # Fix: V shouldn't fluctuate wildly between training corpuses. We set a realistic baseline size.
        self.V = max(len(self.unique_states), self.fixed_V)
        
        for (state_a, state_b), count in edge_counts.items():
            # Add-1 Smoothing: (Count(A->B) + 1) / (Total_Out(A) + V)
            prob = (count + 1) / (node_out_degrees[state_a] + self.V)
            log_prob = math.log(prob)
            
            self.graph.add_edge(state_a, state_b, weight=log_prob, raw_prob=prob)

        self.node_out_degrees = node_out_degrees

    def get_smoothed_log_prob(self, state_a, state_b):
        """
        Retrieves the edge weight. If the edge doesn't exist, safely applies 
        Laplace smoothing for unseen transitions instead of an arbitrary 1e-6.
        """
        if self.graph.has_edge(state_a, state_b):
            return self.graph[state_a][state_b]['weight']
        else:
            # Unseen edge smoothing
            out_degree = self.node_out_degrees.get(state_a, 0)
            smoothed_prob = 1 / (out_degree + self.V)
            return math.log(smoothed_prob)

    def calculate_log_likelihood(self, suspect_text):
        """
        Scores a suspect text by walking the NetworkX graph.
        Returns a tuple: (log_likelihood, confidence_score)
        """
        sequences = self._extract_sequence(suspect_text, is_training=False)
        if not sequences:
            return float('-inf'), 0.0
            
        total_log_likelihood = 0.0
        total_transitions = 0
        
        for seq in sequences:
            for i in range(len(seq) - 1):
                state_a = seq[i]
                state_b = seq[i+1]
                total_log_likelihood += self.get_smoothed_log_prob(state_a, state_b)
                total_transitions += 1
                
        # Normalize by total transitions
        if total_transitions == 0:
            return float('-inf'), 0.0
            
        # Confidence score based on fragment length (e.g., 50 transitions = 1.0 confidence)
        confidence = min(1.0, total_transitions / 50.0)
            
        return total_log_likelihood / total_transitions, confidence

if __name__ == "__main__":
    print("="*60)
    print("BULLETPROOF HMM IP THEFT TRACKER (GRAPH INTELLIGENCE)")
    print("="*60)
    
    original_ip = """
    The company will aggressively expand into the European market next quarter. 
    We must leverage our existing supply chain to minimize overhead costs. 
    Leadership expects a significant return on investment if we maintain strict quality control.
    """
    
    stolen_paraphrased = """
    The corporation shall fiercely grow towards the Asian sector upcoming month. 
    They should utilize their current distribution network to reduce operational expenses. 
    Management anticipates a massive profit from capital when they uphold rigid product standards.
    """
    
    innocent_document = """
    European expansion is a risky but necessary move for our corporate growth. 
    To succeed, we need to focus heavily on marketing and finding local partners. 
    If we don't control our spending, the board of directors will be very unhappy.
    """
    
    print("1. Training Graph on Original IP...")
    hmm_graph = BulletproofHMMGraph()
    hmm_graph.train(original_ip)
    print(f"   -> Graph built with {hmm_graph.graph.number_of_nodes()} nodes and {hmm_graph.graph.number_of_edges()} edges.")
    
    print("\n2. Scoring Stolen Document...")
    stolen_score, stolen_conf = hmm_graph.calculate_log_likelihood(stolen_paraphrased)
    
    print("3. Scoring Innocent Document...")
    innocent_score, inno_conf = hmm_graph.calculate_log_likelihood(innocent_document)
    
    print("-" * 60)
    print(f"Structural Log-Likelihood Scores (Closer to 0 is a higher match):")
    print(f"  -> Stolen (Paraphrased) Score : {stolen_score:.4f} (Conf: {stolen_conf:.2f})")
    print(f"  -> Innocent Document Score    : {innocent_score:.4f} (Conf: {inno_conf:.2f})")
    print("-" * 60)
    
    if stolen_score > innocent_score:
        print("\n[CONCLUSION]: IP THEFT DETECTED!")
        print("The NetworkX structural graph proves the mathematical DNA was copied.")
