import streamlit as st
import json
import os

st.set_page_config(page_title="Synoptics: Doctrinal DAG Merge", page_icon="🔀", layout="wide")

st.title("Synoptics Doctrinal DAG")
st.caption("Newman Resolution Engine - Topological Merge Visualization")

# Load data
data_path = os.path.join("research", "doctrinal-development", "lcms_reunification.json")
try:
    with open(data_path, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    st.error(f"Could not find {data_path}. Ensure you're running this from the Synoptics root.")
    st.stop()

# Header metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Target Graph", data.get("target_graph", "Unknown"))
with col2:
    st.metric("Graph Isomorphism", data.get("graph_isomorphism", {}).get("match_percentage", "0%"))

st.divider()

# Shared Nodes (Isomorphism)
with st.container(border=True):
    st.subheader("Shared Nodes (Isomorphic Core)")
    shared = data.get("graph_isomorphism", {}).get("shared_nodes", [])
    st.pills("Master Branch Matches", shared, disabled=True, default=shared)

# Collisions & Resolutions
st.subheader("Detected Collisions & Newman Resolutions")

collisions = data.get("detected_collisions", [])
resolutions = data.get("newman_resolutions", [])

# Render side-by-side collision cards
for idx, col_data in enumerate(collisions):
    lcms_node = col_data.get("lcms_node", "")
    cath_node = col_data.get("catholic_node", "")
    edge = col_data.get("edge_type", "")
    
    # Find matching resolution
    res_data = next((r for r in resolutions if lcms_node in r.get("collision", [])), None)
    
    with st.container(border=True):
        st.markdown(f"### Collision {idx + 1}: `{edge}`")
        c1, c2, c3 = st.columns([2, 1, 2])
        
        with c1:
            st.error(f"**Fork Node (LCMS):**\n\n{lcms_node}")
        with c2:
            st.markdown("<h1 style='text-align: center; color: red;'>↔</h1>", unsafe_allow_html=True)
        with c3:
            st.info(f"**Master Node (Catholic):**\n\n{cath_node}")
            
        if res_data:
            st.divider()
            res_status = res_data.get("resolution", "")
            hop = res_data.get("higher_order_principle", "")
            context = res_data.get("context_shift", "")
            
            st.markdown(f"#### 🕊️ Newman Resolution: `{res_status}`")
            st.success(f"**Higher Order Principle:** {hop}\n\n**Context Shift:** {context}")

st.divider()

# Mermaid Graph
st.subheader("Topological Graph View")

mermaid_code = """
graph TD
    classDef master fill:#1e4b85,stroke:#fff,color:#fff;
    classDef fork fill:#851e1e,stroke:#fff,color:#fff;
    classDef shared fill:#2b7a3d,stroke:#fff,color:#fff;
    classDef hop fill:#e6a817,stroke:#333,color:#333;

    %% Shared Core
"""
for node in shared:
    mermaid_code += f"    {node}:::shared\n"

mermaid_code += "\n    %% Collisions\n"
for c in collisions:
    mermaid_code += f"    {c['catholic_node']}:::master\n"
    mermaid_code += f"    {c['lcms_node']}:::fork\n"
    mermaid_code += f"    {c['lcms_node']} -- {c['edge_type']} --- {c['catholic_node']}\n"

mermaid_code += "\n    %% Newman Synthesis\n"
for r in resolutions:
    hop = r['higher_order_principle']
    mermaid_code += f"    {hop}:::hop\n"
    col_nodes = r['collision']
    for n in col_nodes:
        mermaid_code += f"    {hop} -. Synthesizes .-> {n}\n"

st.markdown(f"```mermaid\n{mermaid_code}\n```")

