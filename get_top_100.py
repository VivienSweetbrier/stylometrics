import sys
from pathlib import Path
BASE_DIR = Path("c:/Users/Vivian/Desktop/Synoptics")
sys.path.append(str(BASE_DIR))

from src.agents.intelligence_core import StylometricIntelligence

intel = StylometricIntelligence()
results = intel.run_global_delta()

# Filter out same-domain matches
filtered_results = []
for r in results:
    s_domain = r['source'].split('_')[0]
    t_domain = r['target'].split('_')[0]
    if s_domain != t_domain and "Fragments" not in r["source"] and "Fragments" not in r["target"]:
        # Skip mormon explicitly
        if "MORMON" not in r['source'].upper() and "MORMON" not in r['target'].upper() and \
           "NEPHI" not in r['source'].upper() and "NEPHI" not in r['target'].upper() and \
           "ALMA" not in r['source'].upper() and "ALMA" not in r['target'].upper() and \
           "MORONI" not in r['source'].upper() and "MORONI" not in r['target'].upper():
            filtered_results.append(r)

# Take top 100
top_100 = filtered_results[:100]

with open("notebooks/top_100_similarities.md", "w", encoding="utf-8") as f:
    f.write("# Top 100 Most Important Syntactic Similarities (Global Delta)\n\n")
    for i, r in enumerate(top_100):
        f.write(f"### #{i+1}: {r['source']} <--> {r['target']}\n")
        f.write(f"- **Similarity:** {r['similarity']:.2f}%\n")
        f.write(f"- **Disruptiveness:** {r['disruptiveness']:.2f}\n\n")

print("Finished generating top 100.")
