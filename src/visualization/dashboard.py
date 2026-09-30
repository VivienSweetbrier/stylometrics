import streamlit as st
import pandas as pd
import json
import sqlite3
import os
import networkx as nx
import matplotlib.pyplot as plt

# Configuration
st.set_page_config(page_title="Mythology Pipeline Dashboard", layout="wide")

st.title("Mythology Pipeline Interactive Dashboard")

@st.cache_data
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

@st.cache_data
def load_csv(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return None

@st.cache_data
def load_db_data(db_path, query, params=()):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    return None

def render_phylogenetic_tree():
    st.header("Phylogenetic Tree")
    
    png_path = "data/processed/global_graph/phylogenetic_tree.png"
    json_path = "data/processed/global_graph/phylogenetic_tree.json"
    
    if os.path.exists(png_path):
        st.image(png_path, caption="Phylogenetic Tree")
    elif os.path.exists(json_path):
        data = load_json(json_path)
        st.json(data)
    else:
        st.warning(f"Phylogenetic tree data not found. Looked for {png_path} or {json_path}")

def render_knowledge_graph():
    st.header("Knowledge Graph")
    nodes_path = "data/processed/global_graph/nodes.csv"
    edges_path = "data/processed/global_graph/edges.csv"
    
    nodes_df = load_csv(nodes_path)
    edges_df = load_csv(edges_path)
    
    if nodes_df is not None and edges_df is not None:
        st.write(f"Loaded {len(nodes_df)} nodes and {len(edges_df)} edges.")
        
        G = nx.Graph()
        
        if 'id' in nodes_df.columns:
            for _, row in nodes_df.iterrows():
                G.add_node(row['id'], label=row.get('label', row['id']))
                
        if 'source' in edges_df.columns and 'target' in edges_df.columns:
            for _, row in edges_df.iterrows():
                G.add_edge(row['source'], row['target'], weight=row.get('weight', 1))
                
        if len(G.nodes) > 0:
            fig, ax = plt.subplots(figsize=(10, 8))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=False, node_size=20, alpha=0.6, ax=ax)
            st.pyplot(fig)
        else:
            st.warning("Graph data found, but it is empty or missing required columns.")
    else:
        st.warning(f"Knowledge graph data not found. Looked for {nodes_path} and {edges_path}")

def render_orality_analysis():
    st.header("Orality (HMM) Analysis")
    
    db_options = [
        "data/processed/homer.db",
        "data/processed/synoptics.db"
    ]
    
    available_dbs = [db for db in db_options if os.path.exists(db)]
    
    if not available_dbs:
        st.warning("No processed databases found for HMM analysis.")
        return
        
    selected_db = st.selectbox("Select Database", available_dbs)
    
    # In case the table is named differently or we need to find books
    tables_df = load_db_data(selected_db, "SELECT name FROM sqlite_master WHERE type='table'")
    tables = tables_df['name'].tolist() if tables_df is not None else []
    
    hmm_table = "hmm_states" if "hmm_states" in tables else "tokens"
    book_col = "book"
    
    try:
        books_df = load_db_data(selected_db, f"SELECT DISTINCT {book_col} FROM {hmm_table}")
        if books_df is not None and not books_df.empty:
            books = books_df[book_col].tolist()
            selected_book = st.selectbox("Select Book", books)
            
            query_hmm = f"SELECT position_index, hmm_state FROM {hmm_table} WHERE {book_col} = ? ORDER BY position_index"
            hmm_df = load_db_data(selected_db, query_hmm, (selected_book,))
            
            if hmm_df is not None and not hmm_df.empty:
                st.line_chart(data=hmm_df, x="position_index", y="hmm_state")
            else:
                st.warning("No HMM state data found for the selected book.")
        else:
            st.warning(f"Could not find '{book_col}' column or data in {hmm_table} table.")
    except Exception as e:
        st.warning(f"Error querying database: {e}")


tab1, tab2, tab3 = st.tabs(["Phylogenetic Tree", "Knowledge Graph", "Orality Analysis"])

with tab1:
    render_phylogenetic_tree()
    
with tab2:
    render_knowledge_graph()
    
with tab3:
    render_orality_analysis()
