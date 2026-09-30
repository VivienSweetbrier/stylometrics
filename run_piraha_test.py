import sys
from pathlib import Path
BASE_DIR = Path("c:/Users/Vivian/Desktop/Synoptics")
sys.path.append(str(BASE_DIR))

from src.agents.intelligence_core import StylometricIntelligence

intel = StylometricIntelligence()
results = intel.run_global_delta()

piraha_findings = []
for r in results:
    s = r['source'].upper()
    t = r['target'].upper()
    if 'PIRAHA' in s or 'PIRAHA' in t:
        piraha_findings.append(r)

if not piraha_findings:
    report = "# The Null-Hypothesis Test: Pirahã vs. The Global Matrix\n\nNo Pirahã database was successfully ingested or it contains no morphology data."
else:
    # Sort piraha findings by similarity
    piraha_findings.sort(key=lambda x: x['similarity'], reverse=True)

    report = "# The Null-Hypothesis Test: Pirahã vs. The Global Matrix\n\n"
    report += "The Pirahã are a hunter-gatherer tribe of the Amazon Basin, famous for having a language with no numbers, colors, or deep past/creation myths. This test pits their syntax against the entire global matrix to see if they possess any structural mythological crossover.\n\n"

    # Highest similarity
    report += "## Highest Syntactic Similarities\n"
    for i, r in enumerate(piraha_findings[:10]):
        report += f"### #{i+1}: {r['source']} <--> {r['target']} (Similarity: {r['similarity']:.2f}%)\n"

    # Lowest similarity
    report += "\n## Lowest Syntactic Similarities (Absolute Repulsion)\n"
    for i, r in enumerate(reversed(piraha_findings[-10:])):
        report += f"### #{len(piraha_findings)-i}: {r['source']} <--> {r['target']} (Similarity: {r['similarity']:.2f}%)\n"

with open("notebooks/piraha_test_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Done generating Piraha report.")
