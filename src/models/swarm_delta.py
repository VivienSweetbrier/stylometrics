"""
SwarmDelta: heuristic stylometric distances and similarity clusters for traces.
Function words, punctuation, and formatting can suggest resemblance, not establish
identity, shared models, common control, or coordinated behavior.
"""

import re
from numbers import Real
import numpy as np
import pandas as pd
from itertools import combinations
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from sklearn.cluster import AgglomerativeClustering

class SwarmDeltaEngine:
    SIMILARITY_WARNING = (
        "Uncalibrated stylometric similarity only; not evidence of shared identity, "
        "model, prompt, control, or coordination. Scores and thresholds depend on "
        "the supplied corpus, language, topic, text length, and formatting. "
        "Legacy sybil_groups/sybil_threshold names do not establish Sybil activity."
    )

    # Heuristic function words and discourse markers (English-centric).
    DEFAULT_FUNCTION_WORDS = [
        "the", "of", "and", "to", "a", "in", "that", "is", "was", "he", "for", "it", 
        "with", "as", "his", "on", "be", "at", "by", "i", "this", "had", "not", "are", 
        "but", "from", "or", "have", "an", "they", "which", "one", "you", "were", "her", 
        "all", "she", "there", "would", "their", "we", "him", "been", "has", "when", 
        "who", "will", "more", "no", "if", "out", "so", "said", "what", "up", "its", 
        "about", "into", "than", "them", "can", "only", "other", "new", "some", "could", 
        "time", "these", "two", "may", "then", "do", "first", "any", "my", "now", "such", 
        "like", "our", "over", "man", "me", "even", "most", "made", "after", "also", 
        "did", "many", "before", "must", "through", "back", "years", "where", "much", 
        "your", "way", "well", "down", "should", "because", "each", "just", "those", 
        "people", "how", "too", "little", "state", "good", "very", "make", "world", 
        "still", "own", "see", "men", "work", "long", "get", "here", "between", "both", 
        "life", "being", "under", "never", "day", "same", "another", "know", "while", 
        "last", "might", "us", "great", "old", "year", "off", "come", "since", "against", 
        "go", "came", "right", "used", "take", "three", "himself", "few", "furthermore", 
        "however", "crucial", "delve", "essentially", "notably", "specifically", "overall"
    ]

    def __init__(self, function_words: Optional[List[str]] = None, sybil_threshold: float = 0.75):
        if (isinstance(sybil_threshold, bool) or not isinstance(sybil_threshold, Real)
                or not np.isfinite(sybil_threshold) or sybil_threshold < 0):
            raise ValueError("sybil_threshold must be a finite nonnegative number.")
        self.function_words = function_words or self.DEFAULT_FUNCTION_WORDS
        self.sybil_threshold = sybil_threshold

    def extract_agent_features(self, text: str) -> Dict[str, float]:
        """
        Extracts relative frequencies of function words, punctuation, and structural habits.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        total_words = max(len(words), 1)
        word_counts = Counter(words)

        features = {}

        # 1. Function word relative frequencies (scaled per 1,000 words)
        for fw in self.function_words:
            features[f"fw_{fw}"] = (word_counts.get(fw, 0) / total_words) * 1000.0

        # 2. Punctuation cadence
        char_count = max(len(text), 1)
        features["punct_comma"] = (text.count(',') / char_count) * 1000.0
        features["punct_semicolon"] = (text.count(';') / char_count) * 1000.0
        features["punct_colon"] = (text.count(':') / char_count) * 1000.0
        features["punct_dash"] = (len(re.findall(r'—|–|--', text)) / char_count) * 1000.0
        features["punct_parentheses"] = (text.count('(') / char_count) * 1000.0
        features["punct_exclamation"] = (text.count('!') / char_count) * 1000.0
        features["punct_question"] = (text.count('?') / char_count) * 1000.0

        # 3. Structural formatting ticks (markdown habits)
        features["struct_bullet_lines"] = (len(re.findall(r'^\s*[-*+]\s+', text, flags=re.MULTILINE)) / total_words) * 1000.0
        features["struct_numbered_lines"] = (len(re.findall(r'^\s*\d+\.\s+', text, flags=re.MULTILINE)) / total_words) * 1000.0
        features["struct_code_blocks"] = text.count('```')
        features["struct_bold_words"] = len(re.findall(r'\*\*[^*]+\*\*', text))

        # 4. Lexical diversity
        features["lex_ttr"] = len(word_counts) / total_words

        return features

    def compute_burrows_delta(self, agent_corpus: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calculates corpus-relative, uncalibrated Burrows' Delta distances.
        Input: agent_corpus dict mapping agent_id -> concatenated message texts.
        Raises ValueError when fewer than two profiles or no variable features
        are available; identical profiles are not evidence of shared identity.
        Returns:
            - delta_matrix: NxN DataFrame of Burrows' Delta distances
            - z_score_df: Agent feature Z-scores DataFrame
        """
        if len(agent_corpus) < 2:
            raise ValueError("Burrows' Delta requires at least 2 distinct agents.")

        agents = list(agent_corpus.keys())
        raw_feature_rows = []

        for agent in agents:
            feats = self.extract_agent_features(agent_corpus[agent])
            raw_feature_rows.append(feats)

        df_raw = pd.DataFrame(raw_feature_rows, index=agents)

        # Drop features with 0 variance across all agents
        feature_std = df_raw.std(axis=0)
        valid_cols = feature_std[feature_std > 1e-9].index
        if len(valid_cols) == 0:
            raise ValueError(
                "Insufficient data: no stylometric features have nonzero variance. "
                "Identical feature profiles do not establish shared identity."
            )
        df_filtered = df_raw[valid_cols]

        means = df_filtered.mean(axis=0)
        stds = df_filtered.std(axis=0)

        # Standard Z-Score normalization
        z_scores = (df_filtered - means) / stds

        n_features = len(valid_cols)
        n_agents = len(agents)
        delta_matrix = pd.DataFrame(np.zeros((n_agents, n_agents)), index=agents, columns=agents)

        # Compute pairwise Manhattan distances normalized by feature count
        for a1, a2 in combinations(agents, 2):
            diff = np.abs(z_scores.loc[a1] - z_scores.loc[a2])
            delta = float(np.sum(diff) / n_features)
            delta_matrix.loc[a1, a2] = delta
            delta_matrix.loc[a2, a1] = delta

        for frame in (delta_matrix, z_scores):
            frame.attrs.update(calibrated=False, warnings=[self.SIMILARITY_WARNING])
        return delta_matrix, z_scores

    def cluster_swarm_identities(self, delta_matrix: pd.DataFrame) -> Dict[str, Any]:
        """
        Groups similar profiles using an uncalibrated average-linkage threshold.
        Legacy method and sybil_* keys are retained for compatibility only.
        A cluster is not an identity, model attribution, or coordination finding.
        """
        if not isinstance(delta_matrix, pd.DataFrame):
            raise ValueError("Distance matrix must be a labeled DataFrame.")
        if delta_matrix.shape[0] != delta_matrix.shape[1]:
            raise ValueError("Distance matrix must be square.")
        if (not delta_matrix.index.is_unique or not delta_matrix.columns.is_unique
                or not delta_matrix.index.equals(delta_matrix.columns)):
            raise ValueError("Distance matrix labels must be unique and match in the same order.")
        if delta_matrix.index.to_frame(index=False).isna().to_numpy().any():
            raise ValueError("Distance matrix labels must not be missing.")
        dist_array = delta_matrix.to_numpy()
        if (not np.issubdtype(dist_array.dtype, np.number)
                or np.iscomplexobj(dist_array)):
            raise ValueError("Distance matrix must contain real numeric distances.")
        if not np.isfinite(dist_array).all() or (dist_array < 0).any():
            raise ValueError("Distance matrix must contain finite nonnegative distances.")
        if not np.array_equal(dist_array, dist_array.T):
            raise ValueError("Distance matrix must be symmetric.")
        if (np.diag(dist_array) != 0).any():
            raise ValueError("Distance matrix must have a zero diagonal.")

        agents = delta_matrix.index.tolist()
        metadata = {
            "calibrated": False,
            "warnings": [self.SIMILARITY_WARNING],
            "insufficient_data": len(agents) < 2,
        }
        if len(agents) < 2:
            return {
                "total_agents": len(agents), "num_clusters": 0,
                "clusters": {}, "sybil_groups": [], "similarity_groups": [],
                "sybil_threshold": self.sybil_threshold, **metadata,
            }

        # Precomputed distance clustering
        clustering = AgglomerativeClustering(
            metric='precomputed',
            linkage='average',
            distance_threshold=self.sybil_threshold,
            n_clusters=None
        )
        labels = clustering.fit_predict(dist_array)

        clusters = {}
        for agent, label in zip(agents, labels):
            lbl_key = f"Cluster_{label}"
            if lbl_key not in clusters:
                clusters[lbl_key] = []
            clusters[lbl_key].append(agent)

        # Legacy sybil_groups contains heuristic multi-profile similarity groups.
        sybil_groups = [
            {
                "cluster_name": k,
                "agents": v,
                "agent_count": len(v),
                "pairwise_delta_mean": float(delta_matrix.loc[v, v].values[np.triu_indices(len(v), k=1)].mean()) if len(v) > 1 else 0.0
            }
            for k, v in clusters.items() if len(v) > 1
        ]
        sybil_groups.sort(key=lambda x: x["agent_count"], reverse=True)

        return {
            "total_agents": len(agents),
            "num_clusters": len(clusters),
            "clusters": clusters,
            "sybil_groups": sybil_groups,
            "similarity_groups": sybil_groups,
            "sybil_threshold": self.sybil_threshold,
            **metadata,
        }
