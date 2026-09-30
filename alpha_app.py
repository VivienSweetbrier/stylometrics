import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import plotly.express as px
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import engines
from src.data_loader.ingestion_engine import LegalDocumentIngestor
from src.pipeline.hmm_ip_tracker import BulletproofHMMGraph

# Quantitative/Financial aesthetic
st.set_page_config(page_title="AlphaVector: Financial Intelligence", layout="wide", page_icon="📈")

st.markdown("""
<style>
    /* Dark mode quantitative aesthetic */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    .stAlert {
        border-left: 5px solid #f85149;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 AlphaVector: Hedge Fund & Short-Seller Intelligence")
st.markdown("Early warning signals through quantitative authorship and stylistic baselining.")

st.sidebar.header("Alpha Generation Modules")
module = st.sidebar.radio("Active Engine:", [
    "1. Earnings Call & Shareholder Letter 'Ghosting'",
    "2. Whistleblower Authentication"
])

ingestor = LegalDocumentIngestor(strip_bates=False)

if module == "1. Earnings Call & Shareholder Letter 'Ghosting'":
    st.header("Executive 'Ghosting' Detection")
    st.markdown("Detects when a CEO's shareholder letters or earnings call scripts suddenly deviate from their historical stylistic baseline, indicating crisis PR management or impending departure.")
    
    col1, col2 = st.columns(2)
    with col1:
        baseline_files = st.file_uploader("Upload Historical Baseline (Past Letters/Transcripts)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="ghost_base")
    with col2:
        suspect_file = st.file_uploader("Upload Recent Document (Suspect 'Ghosted' Text)", type=["pdf", "docx", "txt"], key="ghost_susp")
        
    if baseline_files and suspect_file:
        if st.button("Run Stylistic Deviation Analysis"):
            with st.spinner("Training Stylistic Baseline Graph..."):
                baseline_text = ""
                for b_file in baseline_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(b_file.name).suffix) as tb:
                        tb.write(b_file.getvalue())
                        path_b = tb.name
                    rec = ingestor.ingest(path_b)
                    baseline_text += rec['text'] + "\n\n"
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(suspect_file.name).suffix) as ts:
                    ts.write(suspect_file.getvalue())
                    path_s = ts.name
                
                susp_record = ingestor.ingest(path_s)
                
                hmm = BulletproofHMMGraph()
                hmm.train(baseline_text)
                
            with st.spinner("Calculating Deviation..."):
                score, conf = hmm.calculate_log_likelihood(susp_record['text'])
                
                st.success("Analysis Complete.")
                st.metric("Stylistic Conformity Score (Log-Likelihood)", f"{score:.4f}")
                
                if score < -3.5: # Threshold for ghosting
                    st.error("🚨 HIGH DEVIATION DETECTED: PR GHOSTWRITING LIKELY 🚨")
                    st.markdown("The current document significantly deviates from the executive's historical grammatical structure and vocabulary patterns. This strongly indicates the involvement of external crisis management PR or a mental check-out.")
                else:
                    st.info("Style remains consistent with the executive's historical baseline.")

elif module == "2. Whistleblower Authentication":
    st.header("Whistleblower Authentication")
    st.markdown("Cross-references the writing style of an anonymous whistleblower's dossier against the public writings of recently departed executives to verify legitimacy.")
    
    col1, col2 = st.columns(2)
    with col1:
        dossier_file = st.file_uploader("Upload Anonymous Dossier", type=["pdf", "docx", "txt"], key="wb_dossier")
    with col2:
        exec_files = st.file_uploader("Upload Known Executive Writings (LinkedIn/Blogs)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="wb_execs")

    if dossier_file and exec_files:
        if st.button("Run Insider Authentication"):
            with st.spinner("Ingesting Known Executive Baselines..."):
                exec_text = ""
                for e_file in exec_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(e_file.name).suffix) as te:
                        te.write(e_file.getvalue())
                        path_e = te.name
                    rec = ingestor.ingest(path_e)
                    exec_text += rec['text'] + "\n\n"
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(dossier_file.name).suffix) as td:
                    td.write(dossier_file.getvalue())
                    path_d = td.name
                dossier_record = ingestor.ingest(path_d)
                
                hmm_exec = BulletproofHMMGraph()
                hmm_exec.train(exec_text)
                
            with st.spinner("Scoring Dossier against Insider Baselines..."):
                raw_text = dossier_record['text']
                paragraphs = [p.strip() for p in raw_text.split('\n\n') if len(p.strip().split()) > 20]
                
                if not paragraphs:
                    st.warning("Dossier too short for structural analysis.")
                else:
                    results = []
                    total_score = 0
                    for i, para in enumerate(paragraphs):
                        score, conf = hmm_exec.calculate_log_likelihood(para)
                        if score != float('-inf'):
                            total_score += score
                            results.append({
                                "Paragraph": i + 1,
                                "Match Score": score,
                                "Snippet": para[:80] + "..."
                            })
                    
                    df_res = pd.DataFrame(results)
                    if not df_res.empty:
                        avg_score = total_score / len(results)
                        st.success("Authentication Complete.")
                        
                        st.metric("Average Insider Match Score", f"{avg_score:.4f}")
                        
                        if avg_score > -3.0:
                            st.success("✅ LEGITIMATE INSIDER CONFIRMED")
                            st.markdown("The whistleblower's structural grammar aligns closely with the known executive's public writings, indicating this is likely a genuine high-level leak.")
                        else:
                            st.warning("⚠️ POTENTIAL FABRICATION / LOW MATCH")
                            st.markdown("The linguistic patterns do not match the suspected executive. This could be a fabricated plant or a lower-level employee.")
                        
                        st.subheader("Match Score Timeline")
                        fig = px.bar(df_res, x="Paragraph", y="Match Score", title="Grammar Alignment by Dossier Paragraph")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.dataframe(df_res, use_container_width=True)
