import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

# 1. Mock UD-Paleo High-Resolution Output (Sparse Tags)
corpus_san = [
    "NOUN|Class=Shape_Long", "VERB|Evident=MythicTime", "PREP|Spatial=Under", 
    "NOUN|Class=Shape_Flexible", "VERB|Evident=MythicTime"
]

corpus_andamanese = [
    "NOUN|Somatic=Hand", "VERB|Evident=Dream", "PREP|Spatial=Over", 
    "NOUN|Somatic=Head", "VERB|Evident=Dream"
]

corpus_homer = [
    "NOUN|Gender=Masc", "VERB|Tense=Past", "PREP|Direction=Towards", 
    "NOUN|Gender=Fem", "VERB|Tense=Past"
]

# 2. Hierarchical Ontology Mapping (The UD-Paleo Collapse Rules)
ontology_tree = {
    # High-res San -> Parent
    "NOUN|Class=Shape_Long": "NOUN|Feature=Class_System",
    "NOUN|Class=Shape_Flexible": "NOUN|Feature=Class_System",
    "VERB|Evident=MythicTime": "VERB|Feature=Evidentiality",
    "PREP|Spatial=Under": "PREP|Feature=Spatial_Relator",
    
    # High-res Andamanese -> Parent
    "NOUN|Somatic=Hand": "NOUN|Feature=Class_System",
    "NOUN|Somatic=Head": "NOUN|Feature=Class_System",
    "VERB|Evident=Dream": "VERB|Feature=Evidentiality",
    "PREP|Spatial=Over": "PREP|Feature=Spatial_Relator",
    
    # High-res Homer -> Parent
    "NOUN|Gender=Masc": "NOUN|Feature=Gender_System",
    "NOUN|Gender=Fem": "NOUN|Feature=Gender_System",
    "VERB|Tense=Past": "VERB|Feature=Tense_System",
    "PREP|Direction=Towards": "PREP|Feature=Directional"
}

def collapse_to_parent(corpus):
    return [ontology_tree.get(tag, tag) for tag in corpus]

# 3. Vectorization & Matrix Generation Function
def compute_similarity(c1, c2, c3, title):
    all_tags = list(set(c1 + c2 + c3))
    
    def vectorize(c):
        counts = Counter(c)
        return [counts.get(t, 0) for t in all_tags]
        
    vec_san = np.array(vectorize(c1)).reshape(1, -1)
    vec_and = np.array(vectorize(c2)).reshape(1, -1)
    vec_hom = np.array(vectorize(c3)).reshape(1, -1)
    
    sim_san_and = cosine_similarity(vec_san, vec_and)[0][0]
    sim_san_hom = cosine_similarity(vec_san, vec_hom)[0][0]
    
    report = f"## {title}\n"
    report += f"- Dimensionality (Features): {len(all_tags)}\n"
    report += f"- San vs Andamanese Similarity: {sim_san_and * 100:.2f}%\n"
    report += f"- San vs Homer Similarity: {sim_san_hom * 100:.2f}%\n\n"
    return report

output = "# Verification Gate: Dynamic Matrix Projection\n\n"

# Test A: The High-Resolution (Sparse) Matrix
output += compute_similarity(corpus_san, corpus_andamanese, corpus_homer, "Test A: High-Resolution Tagging (Vulnerable State)")

# Test B: The Collapsed (Dense) Matrix
output += compute_similarity(
    collapse_to_parent(corpus_san), 
    collapse_to_parent(corpus_andamanese), 
    collapse_to_parent(corpus_homer), 
    "Test B: Hierarchical Parent Tagging (Remediated State)"
)

with open("notebooks/verification_gate_report.md", "w", encoding="utf-8") as f:
    f.write(output)

print("Verification complete.")
