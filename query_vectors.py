import sys
from pathlib import Path
BASE_DIR = Path("c:/Users/Vivian/Desktop/Synoptics")
sys.path.append(str(BASE_DIR))

from src.agents.intelligence_core import StylometricIntelligence

intel = StylometricIntelligence()
results = intel.run_global_delta()

print("\n=== KET VS DINE (NAVAJO/DENE) ===")
for r in results:
    if ("KET" in r["source"].upper() or "YENISEIAN" in r["source"].upper() or "DINE" in r["source"].upper() or "DENE" in r["source"].upper()) and \
       ("KET" in r["target"].upper() or "YENISEIAN" in r["target"].upper() or "DINE" in r["target"].upper() or "DENE" in r["target"].upper()):
        print(f"{r['source']} vs {r['target']} | Sim: {r['similarity']:.2f}% | Disruption: {r['disruptiveness']:.2f}")

print("\n=== OTHER ASTONISHING ANOMALIES (Top 20) ===")
count = 0
for r in results:
    if r['similarity'] < 99.99 and "Fragments" not in r["source"] and "Fragments" not in r["target"]:
        # Filter out self-matches like MORMON vs MORMON
        if r['source'].split('_')[0] != r['target'].split('_')[0]:
            print(f"#{count+1}: {r['source']} vs {r['target']} | Sim: {r['similarity']:.2f}% | Disruption: {r['disruptiveness']:.2f}")
            count += 1
            if count >= 20:
                break
