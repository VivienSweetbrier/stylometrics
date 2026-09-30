import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import plotly.express as px
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import our new LegalTech engines
from src.data_loader.ingestion_engine import LegalDocumentIngestor
from src.pipeline.unified_document_graph import UnifiedDocumentGraph
from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

st.set_page_config(page_title="TruthVector: Legal Forensics", layout="wide", page_icon="⚖️")

st.title("⚖️ TruthVector: Legal Forensics Dashboard")
st.markdown("Mathematical verification of authorship, forgery, and IP theft under the Daubert Standard.")

st.sidebar.header("Forensic Modules")
module = st.sidebar.radio("Active Engine:", [
    "1. Forgery Detection (Unified Document Graph)", 
    "2. IP Theft Tracker (Hidden Markov Model)",
    "3. Authorship Attribution (Markov Classification)"
])

# Initialize Engines
ingestor = LegalDocumentIngestor(strip_bates=True)

if module == "1. Forgery Detection (Unified Document Graph)":
    st.header("Document Forgery & Anomaly Detection")
    st.markdown("Identifies post-hoc insertions and coerced text by mapping the unconscious syntactic dependency graph of the document.")
    
    uploaded_file = st.file_uploader("Upload Questioned Document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    chunk_size = st.slider("Anomaly Scanning Window (Sentences)", min_value=2, max_value=20, value=3)
    
    if uploaded_file is not None:
        if st.button("Run Forensic Analysis"):
            with st.spinner("Establishing Chain of Custody & Ingesting Document..."):
                # Save uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Ingest and Clean
                    doc_record = ingestor.ingest(tmp_path)
                    
                    st.success("Ingestion Complete.")
                    st.info(f"**Chain of Custody SHA-256 Hash:** `{doc_record['sha256_hash']}`")
                    
                    with st.spinner("Building Unified Document Graph (spaCy + NetworkX)..."):
                        udg = UnifiedDocumentGraph()
                        udg.build_graph(doc_record['text'])
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Graph Nodes (Tokens)", udg.graph.number_of_nodes())
                        col2.metric("Graph Edges (Syntax/Sequence)", udg.graph.number_of_edges())
                        
                    with st.spinner("Scanning for Structural Anomalies..."):
                        results = udg.scan_for_structural_anomalies(chunk_size=chunk_size)
                        
                        if results:
                            # Visualization
                            df_res = pd.DataFrame(results)
                            # Convert range to a simpler index for the x-axis
                            df_res['chunk_id'] = df_res.index
                            
                            fig = px.line(df_res.sort_index(ascending=True), x='chunk_id', y='z_score', 
                                          title="Syntactic Variance (Z-Score)",
                                          labels={'chunk_id': 'Window Index', 'z_score': 'Standard Deviations from Mean'})
                            
                            fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Significant Anomaly (> 3.0)")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.subheader("Top 3 Mathematically Probable Forgeries")
                            for i, res in enumerate(results[:3]):
                                st.error(f"**#{i+1}: {res['range']}**")
                                st.markdown(f"**Z-Score:** `+{res['z_score']:.2f} Standard Deviations`")
                                st.markdown(f"**Snippet:** {res['preview']}")
                                
                            # GENERATE AND DOWNLOAD PDF REPORT
                            st.markdown("---")
                            st.subheader("Court Exhibits")
                            report_path = f"TruthVector_Report_{doc_record['sha256_hash'][:8]}.pdf"
                            
                            from src.pipeline.report_generator import generate_forensic_report
                            generate_forensic_report(doc_record, results, report_path)
                            
                            with open(report_path, "rb") as pdf_file:
                                st.download_button(
                                    label="📄 Download Daubert Expert Report (PDF)",
                                    data=pdf_file,
                                    file_name=report_path,
                                    mime="application/pdf",
                                    type="primary"
                                )
                        else:
                            st.warning("Document too short to extract anomalies.")
                except Exception as e:
                    st.error(f"Pipeline Error: {e}")

elif module == "2. IP Theft Tracker (Hidden Markov Model)":
    st.header("Structural IP Theft & Plagiarism")
    st.markdown("Proves structural copyright infringement even if the vocabulary was completely rewritten using a thesaurus or LLM.")
    
    col1, col2 = st.columns(2)
    with col1:
        baseline_file = st.file_uploader("Upload Original IP (Baseline)", type=["pdf", "docx", "txt"], key="base")
    with col2:
        suspect_file = st.file_uploader("Upload Suspect Document (Paraphrased)", type=["pdf", "docx", "txt"], key="susp")
        
    if baseline_file and suspect_file:
        if st.button("Run HMM Structural Match"):
            with st.spinner("Training Graph on Original IP..."):
                # Save temp files
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(baseline_file.name).suffix) as tb:
                    tb.write(baseline_file.getvalue())
                    path_b = tb.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(suspect_file.name).suffix) as ts:
                    ts.write(suspect_file.getvalue())
                    path_s = ts.name
                
                # Ingest
                base_record = ingestor.ingest(path_b)
                susp_record = ingestor.ingest(path_s)
                
                # Train HMM
                hmm = BulletproofHMMGraph()
                hmm.train(base_record['text'])
                
            with st.spinner("Scoring Suspect Document against Original DNA..."):
                score, conf = hmm.calculate_log_likelihood(susp_record['text'])
                
                st.success("Analysis Complete.")
                st.metric("Log-Likelihood Match Score", f"{score:.4f}")
                
                if score > -3.0:  # Arbitrary threshold for demo purposes
                    st.error("🚨 HIGH PROBABILITY OF STRUCTURAL THEFT DETECTED 🚨")
                    st.markdown("The underlying grammatical transitions match the Original IP too closely to be natural, suggesting heavy paraphrasing of the stolen sequence.")
                else:
                    st.info("Structure appears natural and sufficiently divergent from the Original IP.")

elif module == "3. Authorship Attribution (Markov Classification)":
    st.header("Authorship Attribution & Literary Forensics")
    st.markdown("Resolves authorship disputes and collaboration boundaries by comparing structural grammar (Markov Chains) of multiple authors against a questioned text.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        author_a_file = st.file_uploader("Upload Author A (Baseline)", type=["pdf", "docx", "txt"], key="auth_a")
    with col2:
        author_b_file = st.file_uploader("Upload Author B (Baseline)", type=["pdf", "docx", "txt"], key="auth_b")
    with col3:
        questioned_file = st.file_uploader("Upload Questioned Document", type=["pdf", "docx", "txt"], key="quest")
        
    if author_a_file and author_b_file and questioned_file:
        if st.button("Run Authorship Classification"):
            with st.spinner("Ingesting & Training Markov Models for Authors..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(author_a_file.name).suffix) as ta:
                    ta.write(author_a_file.getvalue())
                    path_a = ta.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(author_b_file.name).suffix) as tb:
                    tb.write(author_b_file.getvalue())
                    path_b = tb.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(questioned_file.name).suffix) as tq:
                    tq.write(questioned_file.getvalue())
                    path_q = tq.name
                
                record_a = ingestor.ingest(path_a)
                record_b = ingestor.ingest(path_b)
                record_q = ingestor.ingest(path_q)
                
                hmm_a = BulletproofHMMGraph()
                hmm_a.train(record_a['text'])
                
                hmm_b = BulletproofHMMGraph()
                hmm_b.train(record_b['text'])
                
            with st.spinner("Chunking Questioned Document and Scoring..."):
                raw_text = record_q['text']
                # Naive chunking by double newline to approximate paragraphs/scenes
                paragraphs = [p.strip() for p in raw_text.split('\n\n') if len(p.strip().split()) > 20]
                
                if not paragraphs:
                    st.warning("Could not extract sufficiently large chunks for analysis.")
                else:
                    results = []
                    for i, para in enumerate(paragraphs):
                        score_a, conf_a = hmm_a.calculate_log_likelihood(para)
                        score_b, conf_b = hmm_b.calculate_log_likelihood(para)
                        
                        if score_a == float('-inf') or score_b == float('-inf'):
                            continue
                            
                        predicted_author = "Author A" if score_a > score_b else "Author B"
                        
                        results.append({
                            "Chunk": i + 1,
                            "Author A Score": score_a,
                            "Author B Score": score_b,
                            "Predicted": predicted_author,
                            "Snippet": para[:80] + "..."
                        })
                    
                    df_res = pd.DataFrame(results)
                    if not df_res.empty:
                        st.success("Classification Complete.")
                        
                        st.subheader("Attribution Map (Chronological)")
                        fig = px.line(df_res, x="Chunk", y=["Author A Score", "Author B Score"], 
                                      title="Log-Likelihood Scores across Text Chunks (Higher is Better Match)",
                                      labels={"value": "Log-Likelihood Score", "variable": "Author Baseline"})
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.subheader("Chunk Breakdown")
                        st.dataframe(df_res[["Chunk", "Predicted", "Author A Score", "Author B Score", "Snippet"]], use_container_width=True)
                        
                        a_count = len(df_res[df_res["Predicted"] == "Author A"])
                        b_count = len(df_res[df_res["Predicted"] == "Author B"])
                        st.markdown(f"**Final Tally:** Author A won {a_count} chunks. Author B won {b_count} chunks.")
                    else:
                        st.warning("Not enough valid data to plot.")
