import os
import sqlite3
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

DB_DIR = BASE_DIR / "data" / "processed"

from src.models.stylometrist_node import fetch_chunked_morphology, _get_top_tags

class StylometricIntelligence:
    def __init__(self):
        # Dynamically load all databases in the processed folder
        self.dbs = list(DB_DIR.glob("*.db"))
        
    def aggregate_corpora(self):
        print("Aggregating multi-corpus morphology...")
        all_chunks = []
        all_books = []
        all_labels = []
        
        for db in self.dbs:
            if not db.exists():
                continue
            chunks, labels, books = fetch_chunked_morphology(chunk_size=1000, db_path=db)
            all_chunks.extend(chunks)
            all_books.extend(books)
            all_labels.extend(labels)
            
        return all_chunks, all_labels, all_books

    def run_global_delta(self):
        chunks, labels, books = self.aggregate_corpora()
        if not chunks:
            print("No data available across corpora.")
            return []
            
        print(f"Extracted {len(chunks)} text chunks across {len(set(books))} distinct texts/books.")
        
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
            
        # Calculate anomalous cross-connections
        anomalies = []
        for i, b1 in enumerate(unique_books):
            for j, b2 in enumerate(unique_books):
                if i >= j:
                    continue
                vec1 = book_z_vectors[b1].reshape(1, -1)
                vec2 = book_z_vectors[b2].reshape(1, -1)
                sim = cosine_similarity(vec1, vec2)[0][0]
                similarity_pct = ((sim + 1) / 2) * 100
                anomalies.append({
                    "source": b1,
                    "target": b2,
                    "similarity": similarity_pct,
                    "disruptiveness": self._score_disruptiveness(b1, b2, similarity_pct)
                })
                
        # Sort by most similar instead of most disruptive
        anomalies.sort(key=lambda x: x['similarity'], reverse=True)
        return anomalies

    def _score_disruptiveness(self, b1, b2, sim):
        """
        Calculates how 'disruptive' a finding is based on expected norms.
        High similarity across vastly different traditions (e.g. Paul vs Gnostic) = High Disruption.
        Low similarity between supposedly same author = High Disruption.
        """
        score = 0.0
        
        pauline = ['ROM', '1CO', '2CO', 'GAL', 'PHP', '1TH', 'PHM', 'EPH', 'COL', '2TH', '1TI', '2TI', 'TIT', 'HEB']
        gnostic = ['THOMAS', 'GINZA_RABBA']
        gospels = ['MAT', 'MRK', 'LUK', 'JHN']
        
        # Cross-tradition high similarities are highly disruptive
        if (b1 in pauline and b2 in gnostic) or (b2 in pauline and b1 in gnostic):
            if sim > 70:
                score += sim * 2
                
        if (b1 in gospels and b2 in gnostic) or (b2 in gospels and b1 in gnostic):
            if sim > 75:
                score += sim * 1.5
                
        # Supposedly same author but low similarity (Pseudepigrapha detection)
        if b1 in pauline and b2 in pauline:
            if sim < 60:
                score += (100 - sim) * 1.5
                
        # Default variance score for unexpected connections
        if score == 0.0:
            if sim > 85: # Random high similarity
                score += sim
            elif sim < 20: # Extreme divergence
                score += (100 - sim) * 0.5
                
        return score

if __name__ == "__main__":
    intel = StylometricIntelligence()
    results = intel.run_global_delta()
    print("\n=== TOP 10 DISRUPTIVE FINDINGS ===")
    for i, res in enumerate(results[:10]):
        print(f"#{i+1}: {res['source']} vs {res['target']} | Sim: {res['similarity']:.1f}% | Disruption: {res['disruptiveness']:.1f}")
