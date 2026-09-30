import re
from pathlib import Path
from pyvis.network import Network
import pandas as pd
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_FILE = BASE_DIR / "data" / "processed" / "markov_topic_results.txt"
OUTPUT_HTML = BASE_DIR / "notebooks" / "synoptic_network.html"
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

def fetch_titles():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT id, title FROM pericopes", conn)
        conn.close()
        return dict(zip(df['id'], df['title']))
    except:
        return {}

def build_network():
    if not RESULTS_FILE.exists():
        print("Error: Could not find LDA results file.")
        return

    titles = fetch_titles()
    
    # Initialize PyVis network
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", select_menu=True, filter_menu=True)
    
    # Add the 3 Latent Sources as massive central nodes
    net.add_node("Source 1", label="Latent Source 1\n(e.g., Markan Spine)", color="#e74c3c", size=50, title="The primary structural narrative spine.")
    net.add_node("Source 2", label="Latent Source 2\n(e.g., Q Document)", color="#3498db", size=50, title="The secondary teaching/sayings spine.")
    net.add_node("Source 3", label="Latent Source 3\n(e.g., L/M/John)", color="#2ecc71", size=50, title="Independent, localized, or Johannine tradition.")
    
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Regex to find: Pericope 1 -> Bound to Source 3 (Sequence Match Prob: 99.4%)
    pattern = r"Pericope (\d+) -> Bound to Source (\d+) \(Sequence Match Prob: ([\d\.]+)%\)"
    matches = re.findall(pattern, content)
    
    print(f"Plotting {len(matches)} pericopes...")
    
    for match in matches:
        p_id = int(match[0])
        dominant_source = f"Source {match[1]}"
        prob = float(match[2])
        
        title = titles.get(p_id, f"Pericope {p_id}")
        node_id = f"P{p_id}"
        
        # Color based on dominant source
        if dominant_source == "Source 1":
            color = "#ff7979"
        elif dominant_source == "Source 2":
            color = "#7ed6df"
        else:
            color = "#badc58"
            
        # If it's a hybrid (low dominant probability), make it stand out
        if prob < 85.0:
            color = "#f9ca24" # Gold for hybrids
            node_label = f"HYBRID: {title}"
            size = 30
        else:
            node_label = title
            size = 15
            
        hover_text = f"{title}\nDominant: {dominant_source} ({prob}%)"
        
        net.add_node(node_id, label=node_label, color=color, size=size, title=hover_text)
        
        # Draw edge
        # The thickness of the line is based on the probability
        net.add_edge(node_id, dominant_source, value=prob, title=f"{prob}% match")

    # Use a physics layout that clusters nodes around their sources
    net.repulsion(node_distance=150, central_gravity=0.2, spring_length=200, spring_strength=0.05, damping=0.09)
    
    net.save_graph(str(OUTPUT_HTML))
    print(f"\n✅ Network Graph successfully generated!")
    print(f"Open this file in your web browser: {OUTPUT_HTML}")

if __name__ == "__main__":
    build_network()
