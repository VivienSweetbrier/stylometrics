from sklearn.cluster import HDBSCAN
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np

class ThreatClusteringEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2', min_cluster_size=3):
        """
        Initializes the clustering engine.
        Using a lightweight sentence transformer for fast semantic embeddings.
        """
        self.model = SentenceTransformer(model_name)
        self.min_cluster_size = min_cluster_size
        self.clusterer = HDBSCAN(min_cluster_size=self.min_cluster_size, metric='euclidean', cluster_selection_method='eom')

    def cluster_documents(self, documents):
        """
        Takes a list of document dicts (must contain 'id' and 'text').
        Returns a DataFrame with clustering results.
        """
        if not documents:
            return pd.DataFrame()
            
        texts = [doc['text'] for doc in documents]
        ids = [doc['id'] for doc in documents]
        
        # 1. Generate Embeddings in safe batches to prevent GPU/RAM OOM
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        
        # 1.5. Dimensionality Reduction (UMAP or PCA)
        try:
            import umap
            reducer = umap.UMAP(n_components=5, random_state=42)
            reduced_embeddings = reducer.fit_transform(embeddings)
        except ImportError:
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=min(5, len(embeddings)))
            reduced_embeddings = reducer.fit_transform(embeddings)

        # 2. Perform HDBSCAN Clustering
        # Automatically detects clusters and handles noise (assigns to -1)
        cluster_labels = self.clusterer.fit_predict(reduced_embeddings)
        
        # Extract probabilities if available
        probabilities = self.clusterer.probabilities_
        
        # 3. Format Results
        results = []
        for i in range(len(documents)):
            res = {
                "id": ids[i],
                "text": texts[i][:200] + "..." if len(texts[i]) > 200 else texts[i], # Snippet for UI
                "cluster_id": cluster_labels[i],
                "confidence": probabilities[i],
            }
            # Append any extra metadata from original docs
            for k, v in documents[i].items():
                if k not in res and k != 'text':
                    res[k] = v
            results.append(res)
            
        df = pd.DataFrame(results)
        
        # Sort so clusters are grouped, with noise (-1) at the end
        df = df.sort_values(by=['cluster_id', 'confidence'], ascending=[False, False])
        
        return df

    def get_cluster_summaries(self, df):
        """
        Generate summary stats for the clusters.
        """
        if df.empty:
            return {}
            
        summary = {}
        for cluster_id, group in df.groupby('cluster_id'):
            if cluster_id == -1:
                label = "Unassigned / Noise"
            else:
                label = f"Actor Group {cluster_id}"
                
            summary[label] = {
                "cluster_id": cluster_id,
                "count": len(group),
                "avg_confidence": group['confidence'].mean()
            }
        return summary

    def detect_stylometric_anomaly(self, baseline_docs, suspect_text):
        """
        Compare a suspect text against a baseline of verified emails using semantic/stylometric embeddings.
        Returns a mock UI-ready structure containing the data frame and intel brief.
        """
        baseline_texts = [doc['text'] for doc in baseline_docs]
        baseline_ids = [doc['id'] for doc in baseline_docs]
        
        # Get embeddings
        all_texts = baseline_texts + [suspect_text]
        embeddings = self.model.encode(all_texts, batch_size=32, show_progress_bar=False)
        
        baseline_embeddings = embeddings[:-1]
        suspect_embedding = embeddings[-1]
        
        # Calculate centroid of baseline
        centroid = np.mean(baseline_embeddings, axis=0)
        
        # Calculate cosine similarity between suspect and baseline centroid
        from numpy.linalg import norm
        cosine_sim = np.dot(suspect_embedding, centroid) / (norm(suspect_embedding) * norm(centroid))
        divergence_score = (1 - cosine_sim) * 100 # Convert to percentage divergence
        
        # Calculate 2D coordinates for UI graphing (UMAP/PCA)
        try:
            import umap
            reducer = umap.UMAP(n_components=2, random_state=42)
        except ImportError:
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=2)
            
        coords_2d = reducer.fit_transform(embeddings)
        
        results = []
        for i in range(len(baseline_docs)):
            results.append({
                'id': baseline_ids[i],
                'type': 'Verified Baseline',
                'x': float(coords_2d[i][0]),
                'y': float(coords_2d[i][1])
            })
            
        results.append({
            'id': 'Suspect Email',
            'type': 'Suspect Email',
            'x': float(coords_2d[-1][0]),
            'y': float(coords_2d[-1][1])
        })
        
        df_results = pd.DataFrame(results)
        
        # If divergence is > 15%, flag as fraud for the demo
        is_fraud = divergence_score > 15.0
        
        intel_briefs = {
            'anomaly_score': float(divergence_score),
            'is_fraud': bool(is_fraud),
            'suspect_text': suspect_text
        }
        
        return df_results, intel_briefs
