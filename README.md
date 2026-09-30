# Synoptics: Neuro-Symbolic Stylometrics and Causal Text Forensics

**Synoptics** is a computational linguistics and causal forensics pipeline designed to map the latent topologies of authorship, textual transmission, and syntactic mutation across large historical and modern corpora.

By integrating Bayesian inference (via Stan), Markov Topic Modeling, and Burrows' Delta with a multi-agent Directed Acyclic Graph (DAG) architecture, Synoptics escapes the limitations of standard stochastic next-token prediction. It functions as a Universal Verification Engine for textual forensics, capable of detecting steganographic anomalies, collaborative attribution patterns, and phylogenetic drift.

## Architecture

The pipeline is driven by a decentralized swarm of specialized nodes:

*   **Ingestion Engine:** Automated scrapers and bulk ingestors (e.g., Homeric treebanks, SEC EDGAR filings, Hebrew and Synoptic parallels).
*   **Stylometrist Node (`stylometrist_node.py` / `homer_burrows_delta.py`):** Computes syntactic distances and high-frequency function word variances to identify distinct authorial signatures.
*   **Statistician Node (`statistician_node.py` / `fatigue.stan`):** Applies Bayesian modeling to detect authorial fatigue, latent source dependencies, and multi-author blending (e.g., resolving the Synoptic Problem or Homeric Question).
*   **Philologist Node (`philologist.py` / `node_phylogenetic_tree.py`):** Constructs evolutionary trees of text mutation, identifying the causal root of linguistic shifts and structural borrowing.
*   **Stegoprobe Engine (`stegoprobe_engine.py`):** Scans for adversarial anomalies and embedded steganographic noise within digital communications.

## Key Capabilities
1.  **Causal Source Modeling:** Moving beyond correlative text comparison to map the exact causal direction of textual inheritance (e.g., modeling 'Q' in Biblical scholarship).
2.  **Adversarial Forensics:** Threat clustering and trajectory drift analysis for modern cyber-communications.
3.  **Neuro-Symbolic Swarm Logic:** Employing discrete, mathematically verified agents to cross-validate findings before resolving the ontology (`node_ontology_resolution.py`).

## Installation & Usage
*(Documentation and environment configurations pending formal release)*
