import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class CyberIntelligenceCore:
    def __init__(self):
        """
        System Intelligence node for procedurally analyzing Cyber Threat clusters.
        """
        # Using a basic TF-IDF vectorizer to extract defining n-grams
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 3), max_features=1000)

    def generate_intelligence_brief(self, df_clusters):
        """
        Takes the DataFrame output from ThreatClusteringEngine and generates an intel brief.
        """
        if df_clusters.empty:
            return {"error": "No data to analyze."}

        briefs = {}
        
        # 1. Analyze Core Clusters (Threat Actors)
        core_clusters = [c for c in df_clusters['cluster_id'].unique() if c != -1]
        
        for cid in core_clusters:
            cluster_data = df_clusters[df_clusters['cluster_id'] == cid]
            texts = cluster_data['text'].tolist()
            
            # Extract TTPs/Keywords
            keywords = self._extract_top_keywords(texts, top_n=5)
            
            # Auto-generate a working name
            working_name = f"Operation {keywords[0].title().replace(' ', '')}" if keywords else f"Unknown-Actor-{cid}"
            
            briefs[cid] = {
                "working_name": working_name,
                "document_count": len(texts),
                "avg_confidence": float(cluster_data['confidence'].mean()),
                "defining_ttps": keywords,
                "hypothesis": self._generate_cluster_hypothesis(working_name, len(texts), keywords)
            }
            
        # 2. Analyze Noise (Potential Splinters / Emerging Threats)
        noise_data = df_clusters[df_clusters['cluster_id'] == -1]
        if not noise_data.empty:
            briefs[-1] = {
                "working_name": "Unassigned Anomalies (Noise)",
                "document_count": len(noise_data),
                "avg_confidence": 0.0,
                "defining_ttps": self._extract_top_keywords(noise_data['text'].tolist(), top_n=5),
                "hypothesis": "These documents do not strongly align with known actor signatures. This high variance suggests either automated randomization (noise generation) or an early-stage pivot by an operator developing a new operational identity."
            }
            
        return briefs

    def _extract_top_keywords(self, texts, top_n=5):
        """
        Extracts the highest TF-IDF scoring terms for a list of texts.
        """
        if not texts or len(texts) == 0:
            return []
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Sum tfidf scores across all documents in this cluster
            summed_tfidf = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
            
            # Get top N indices
            top_indices = summed_tfidf.argsort()[-top_n:][::-1]
            return [feature_names[i] for i in top_indices]
        except ValueError:
            # Handles edge case where texts are entirely stop words or empty
            return ["insufficient-data"]

    def _generate_cluster_hypothesis(self, name, count, keywords):
        """
        Procedurally generates a threat hypothesis based on the cluster's characteristics.
        """
        if count > 10:
            vol = "high volume"
            structure = "a well-established, highly coordinated operational tempo"
        else:
            vol = "low volume"
            structure = "a nascent or tightly controlled operational structure"
            
        key_str = ", ".join(keywords[:3]) if keywords else "unknown methods"
        
        return f"Actor {name} demonstrates {structure} ({count} artifacts). Their stylistic fingerprint heavily indexes on [{key_str}], suggesting a shared ideological substrate or a monolithic toolkit distributed among operators."
