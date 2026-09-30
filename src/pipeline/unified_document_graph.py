import spacy
import networkx as nx
import numpy as np
from collections import Counter, defaultdict
import math
import sys
import hashlib
from sklearn.metrics.pairwise import cosine_similarity

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spacy model: python -m spacy download en_core_web_sm")
    sys.exit(1)

class UnifiedDocumentGraph:
    def __init__(self):
        # Directed graph to hold both sequential and syntactic edges
        self.graph = nx.DiGraph()
        self.document_hash = None
        
    def build_graph(self, text: str):
        """
        Compiles raw text into a Unified Mathematical Graph.
        Nodes = Tokens (Words/Punctuation)
        Edges = Sequence Flow OR Syntactic Dependencies
        """
        self.document_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Fix: Process in chunks to prevent Spacy OOM on large texts
        # Fix 2: Also split massive lines to avoid OOM
        chunk_size = 50000
        chunks = []
        
        # We replace newlines and split by chunks safely
        safe_text = text.replace('\n', ' ')
        for i in range(0, len(safe_text), chunk_size):
            chunks.append(safe_text[i:i+chunk_size])
            
        global_sent_idx = 0
        global_token_idx = 0
        
        # Disable unused pipes to prevent memory bloat
        disabled_pipes = ["ner", "entity_linker", "entity_ruler", "textcat", "lemmatizer"]
        active_pipes = [p for p in nlp.pipe_names if p not in disabled_pipes]
        
        for doc in nlp.pipe(chunks, disable=[p for p in nlp.pipe_names if p not in active_pipes]):
            for sent in doc.sents:
                sent_nodes = []
                token_to_node = {}
                
                for token in sent:
                    # Ignore pure whitespace
                    if token.is_space:
                        continue
                        
                    current_node_id = f"N{global_token_idx}"
                    token_to_node[token.i] = current_node_id
                    sent_nodes.append(current_node_id)
                    
                    # Add Node with linguistic metadata
                    self.graph.add_node(
                        current_node_id, 
                        text=token.text, 
                        pos=token.pos_, 
                        dep=token.dep_,
                        sentence=global_sent_idx
                    )
                    global_token_idx += 1
                    
                for token in sent:
                    if token.is_space:
                        continue
                        
                    current_node_id = token_to_node[token.i]
                    # Add Syntactic Dependency Edge (Head -> Child)
                    if token.head.i != token.i and token.head.i in token_to_node:
                        head_node_id = token_to_node[token.head.i]
                        self.graph.add_edge(head_node_id, current_node_id, edge_type='syntactic_dependency', relation=token.dep_)
                
                # Add Sequential Edges (Word 1 -> Word 2)
                for i in range(len(sent_nodes) - 1):
                    self.graph.add_edge(sent_nodes[i], sent_nodes[i+1], edge_type='sequence')
                    
                global_sent_idx += 1
                
    def extract_structural_motifs(self, sentence_range=None):
        """
        Extracts structural 'motifs' (subgraphs). 
        For example, a common motif is: POS1 --[relation]--> POS2
        This creates a deeply unconscious syntactic fingerprint.
        """
        motifs = Counter()
        
        if sentence_range is None:
            # Full scan
            for u, v, data in self.graph.edges(data=True):
                if data.get('edge_type') == 'syntactic_dependency':
                    pos_u = self.graph.nodes[u].get('pos', 'UNKNOWN')
                    pos_v = self.graph.nodes[v].get('pos', 'UNKNOWN')
                    relation = data.get('relation', 'UNKNOWN')
                    motif = f"{pos_u} --[{relation}]--> {pos_v}"
                    motifs[motif] += 1
            return motifs

        # Targeted scan using successors to avoid O(E) full iteration
        nodes_in_range = {n for n, d in self.graph.nodes(data=True) if d.get('sentence') in sentence_range}
        for u in nodes_in_range:
            for v in self.graph.successors(u):
                data = self.graph.get_edge_data(u, v)
                if data and data.get('edge_type') == 'syntactic_dependency':
                    pos_u = self.graph.nodes[u].get('pos', 'UNKNOWN')
                    pos_v = self.graph.nodes[v].get('pos', 'UNKNOWN')
                    relation = data.get('relation', 'UNKNOWN')
                    motif = f"{pos_u} --[{relation}]--> {pos_v}"
                    motifs[motif] += 1
                
        return motifs
        
    def get_fingerprint(self, top_n=50):
        """
        Extracts the global motif fingerprint for this document.
        Used as a baseline for authorship attribution of other documents or fragments.
        Returns: {motif: relative_frequency}
        """
        global_motifs = self.extract_structural_motifs()
        total_global = sum(global_motifs.values())
        if total_global == 0:
            return {}
            
        top_motifs = [m for m, c in global_motifs.most_common(top_n)]
        fingerprint = {m: global_motifs[m] / total_global for m in top_motifs}
        return fingerprint
        
    def compare_to_baseline(self, baseline_fingerprint):
        """
        Compares the entire current document against a known baseline fingerprint.
        Ideal for validating if a short fragment (like Hand D) matches a specific author (Shakespeare).
        Returns a distance score (0 to 100), where 0 is identical structural DNA.
        """
        if not baseline_fingerprint:
            return 100.0
            
        current_motifs = self.extract_structural_motifs()
        total_current = sum(current_motifs.values())
        
        # If document is empty or has no structural edges
        if total_current == 0:
            return 100.0
            
        # We align vectors based on the top motifs in the BASELINE
        baseline_keys = list(baseline_fingerprint.keys())
        baseline_vec = np.array([baseline_fingerprint[k] for k in baseline_keys]).reshape(1, -1)
        
        current_vec = np.array([current_motifs.get(k, 0) / total_current for k in baseline_keys]).reshape(1, -1)
        
        # If current document has NONE of the baseline motifs
        if not current_vec.any():
            return 100.0
            
        sim = cosine_similarity(baseline_vec, current_vec)[0][0]
        distance = max(0.0, (1.0 - sim) * 100)
        return distance

    def scan_for_structural_anomalies(self, chunk_size=3):
        """
        Scans the document graph in chunks of sentences.
        Compares the motif fingerprint of the chunk against the global graph.
        """
        # Global Fingerprint
        global_motifs = self.extract_structural_motifs()
        total_global = sum(global_motifs.values())
        if total_global == 0:
            return []
            
        # Top 20 motifs define the "Structural DNA"
        top_motifs = [m for m, c in global_motifs.most_common(20)]
        global_vec = np.array([global_motifs[m] / total_global for m in top_motifs]).reshape(1, -1)
        
        # Get total number of sentences
        sentences = set(nx.get_node_attributes(self.graph, 'sentence').values())
        max_sent = max(sentences) if sentences else 0
        
        # Fix: Dynamic chunk sizing for very short documents
        actual_chunk_size = min(chunk_size, max_sent + 1)
        if actual_chunk_size == 0:
            return []
        
        anomalies = []
        raw_distances = []
        
        # Precompute sentence-level text and motifs
        sent_texts = defaultdict(list)
        for n, d in self.graph.nodes(data=True):
            s = d.get('sentence')
            if s is not None:
                sent_texts[s].append((n, d.get('text', '')))
                
        for s in sent_texts:
            # Sort tokens to reconstruct text based on N-index
            sent_texts[s].sort(key=lambda x: int(x[0][1:]))
            sent_texts[s] = " ".join(text for _, text in sent_texts[s])
            
        sent_motifs = {s: self.extract_structural_motifs(sentence_range=[s]) for s in sentences}
        
        # Sliding Window over the Graph (by Sentence Chunks)
        for i in range(0, max_sent + 1 - actual_chunk_size + 1):
            sent_range = range(i, i + actual_chunk_size)
            
            chunk_motifs = Counter()
            for s in sent_range:
                if s in sent_motifs:
                    chunk_motifs.update(sent_motifs[s])
            
            total_chunk = sum(chunk_motifs.values())
            if total_chunk == 0:
                continue
                
            chunk_vec = np.array([chunk_motifs.get(m, 0) / total_chunk for m in top_motifs]).reshape(1, -1)
            
            if not chunk_vec.any():
                distance = 100.0
            else:
                sim = cosine_similarity(global_vec, chunk_vec)[0][0]
                distance = max(0.0, (1.0 - sim) * 100)
            
            # Extract text for context
            chunk_text = " ".join(sent_texts.get(s, "") for s in sent_range).strip()
            preview = chunk_text[:80].replace('\n', ' ') + "..."
            
            anomalies.append({
                'range': f"Sentences {i} to {i + actual_chunk_size - 1}",
                'distance': distance,
                'preview': preview,
                'motifs': chunk_motifs
            })
            raw_distances.append(distance)
            
        # Z-Score Calculation (Daubert Standard)
        if len(raw_distances) > 1:
            mean_dist = np.mean(raw_distances)
            std_dist = np.std(raw_distances)
            # Fix: Use 1e-9 to strictly avoid zero-division and NaNs
            std_dist = max(std_dist, 1e-9) 
            
            for a in anomalies:
                a['z_score'] = (a['distance'] - mean_dist) / std_dist
        else:
            for a in anomalies:
                a['z_score'] = 0.0
                
        anomalies.sort(key=lambda x: x.get('z_score', 0), reverse=True)
        return anomalies

if __name__ == "__main__":
    # The Simulation: A Contract with a Forged Clause
    # The baseline is formal, highly structured legal English.
    # The forged clause uses slightly different syntactic motifs (more passive, different modifiers).
    
    contract_text = """
    This Agreement is entered into by and between the Client and the Contractor. 
    The Contractor agrees to perform the services described in Appendix A. 
    The Client agrees to compensate the Contractor according to the payment schedule. 
    Both parties mutually agree to maintain strict confidentiality regarding all proprietary information. 
    The Contractor shall indemnify the Client against any third-party claims. 
    The Client reserves the right to terminate this Agreement with thirty days written notice. 
    
    The company will not be held responsible for any damages. The damages will be paid by the contractor. The contractor is fully liable. 
    
    This Agreement shall be governed by the laws of the State of Delaware. 
    Any disputes arising under this Agreement shall be resolved through binding arbitration.
    """
    
    print("="*60)
    print("UNIFIED DOCUMENT GRAPH (UDG) FORENSICS")
    print("="*60)
    
    udg = UnifiedDocumentGraph()
    print("1. Parsing Document into Mathematical Graph...")
    udg.build_graph(contract_text)
    print(f"   -> Graph Topology: {udg.graph.number_of_nodes()} Nodes, {udg.graph.number_of_edges()} Edges")
    
    print("\n2. Extracting Subgraph Motifs (Syntactic DNA)...")
    motifs = udg.extract_structural_motifs()
    print(f"   -> Identified {len(motifs)} unique syntactic motifs.")
    print("   -> Top 3 Motifs:")
    for m, c in motifs.most_common(3):
        print(f"      * {m} (used {c} times)")
        
    print("\n3. Scanning Graph for Anomalous Motif Clusters...")
    # Scan using 2-sentence chunks for this short document
    results = udg.scan_for_structural_anomalies(chunk_size=2)
    
    print("\n[TOP STRUCTURAL ANOMALIES]")
    for i, res in enumerate(results[:3]):
        print(f"#{i+1}: {res['range']}")
        print(f"   Z-Score: +{res['z_score']:.2f} Standard Deviations")
        print(f"   Snippet: '{res['preview']}'")
        print("-" * 40)
