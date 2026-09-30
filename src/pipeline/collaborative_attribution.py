import os
import spacy
from hmm_ip_tracker import BulletproofHMMGraph
from unified_document_graph import UnifiedDocumentGraph
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

class CollaborativeAttribution:
    def __init__(self):
        self.author_hmms = {}
        self.author_udg_motifs = {}
        self.top_motifs = []
        self.author_udg_vectors = {}
        
    def train_author(self, author_name, author_text):
        """
        Trains both the HMM and UDG on a known author's baseline text.
        """
        print(f"Training Stylometric Models for {author_name}...")
        
        # Train HMM (Function Word Adjacency + POS)
        hmm = BulletproofHMMGraph()
        hmm.train(author_text)
        self.author_hmms[author_name] = hmm
        
        # Train UDG (Syntactic Dependencies + Function Word WANs)
        udg = UnifiedDocumentGraph()
        udg.build_graph(author_text)
        motifs = udg.extract_structural_motifs()
        self.author_udg_motifs[author_name] = motifs
        
    def _finalize_udg_training(self):
        """
        Prepares the vector space for UDG cosine similarity based on top motifs across all authors.
        """
        global_motifs = Counter()
        for motifs in self.author_udg_motifs.values():
            global_motifs.update(motifs)
            
        # Top 50 motifs represent the combined structural DNA vector space
        self.top_motifs = [m for m, c in global_motifs.most_common(50)]
        
        for author, motifs in self.author_udg_motifs.items():
            total = sum(motifs.values())
            if total == 0:
                vec = np.zeros((1, len(self.top_motifs)))
            else:
                vec = np.array([motifs.get(m, 0) / total for m in self.top_motifs]).reshape(1, -1)
            self.author_udg_vectors[author] = vec
            
    def analyze_scenes(self, scenes):
        """
        Scores a list of scenes against all trained authors.
        scenes: list of dicts [{'name': 'Act 1 Scene 1', 'text': '...'}]
        """
        self._finalize_udg_training()
        results = []
        
        for scene in scenes:
            scene_name = scene['name']
            text = scene['text']
            print(f"Analyzing {scene_name}...")
            
            # 1. HMM Log-Likelihood Scores
            hmm_scores = {}
            hmm_confidences = {}
            for author, hmm in self.author_hmms.items():
                ll, conf = hmm.calculate_log_likelihood(text)
                hmm_scores[author] = ll
                hmm_confidences[author] = conf
                
            # 2. UDG Cosine Similarity Scores
            udg = UnifiedDocumentGraph()
            udg.build_graph(text)
            scene_motifs = udg.extract_structural_motifs()
            total = sum(scene_motifs.values())
            
            udg_scores = {}
            if total > 0:
                scene_vec = np.array([scene_motifs.get(m, 0) / total for m in self.top_motifs]).reshape(1, -1)
                for author, vec in self.author_udg_vectors.items():
                    sim = cosine_similarity(scene_vec, vec)[0][0]
                    udg_scores[author] = sim
            else:
                for author in self.author_hmms.keys():
                    udg_scores[author] = 0.0
                    
            # Determine Top Candidates
            top_hmm_author = max(hmm_scores, key=hmm_scores.get) if hmm_scores else "Unknown"
            top_udg_author = max(udg_scores, key=udg_scores.get) if udg_scores else "Unknown"
            
            results.append({
                'scene': scene_name,
                'hmm_scores': hmm_scores,
                'udg_scores': udg_scores,
                'top_hmm': top_hmm_author,
                'top_udg': top_udg_author
            })
            
        return results

    def generate_report(self, results):
        print("\n" + "="*60)
        print("COLLABORATIVE ATTRIBUTION REPORT")
        print("="*60)
        
        for res in results:
            print(f"\n[{res['scene']}]")
            
            print("  HMM Log-Likelihoods (Function Word Adjacency + POS Transitions):")
            # Sort by highest score first (closest to 0)
            sorted_hmm = sorted(res['hmm_scores'].items(), key=lambda item: item[1], reverse=True)
            for author, score in sorted_hmm:
                print(f"    - {author}: {score:.4f}")
            print(f"    => HMM Verdict: {res['top_hmm']}")
            
            print("  UDG Cosine Similarity (Syntactic Dependencies + WANs):")
            # Sort by highest similarity
            sorted_udg = sorted(res['udg_scores'].items(), key=lambda item: item[1], reverse=True)
            for author, score in sorted_udg:
                print(f"    - {author}: {score:.4f}")
            print(f"    => UDG Verdict: {res['top_udg']}")

if __name__ == "__main__":
    # Example integration test
    sh_baseline = "To be or not to be, that is the question. Whether tis nobler in the mind to suffer the slings and arrows of outrageous fortune."
    fletcher_baseline = "Ye gods, what a terrible burden we bear! I have not the heart to go on with this folly. Let us away."
    
    attribution = CollaborativeAttribution()
    attribution.train_author("Shakespeare", sh_baseline)
    attribution.train_author("Fletcher", fletcher_baseline)
    
    scenes = [
        {"name": "Act 1 Scene 1", "text": "To be or not to be, I ask thee. We suffer outrageous arrows and fortune."},
        {"name": "Act 1 Scene 2", "text": "Ye gods! Let us away from this terrible folly, for I have not the heart."}
    ]
    
    results = attribution.analyze_scenes(scenes)
    attribution.generate_report(results)
