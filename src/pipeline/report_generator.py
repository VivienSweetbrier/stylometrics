import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

def generate_forensic_report(doc_record: dict, anomalies: list, output_path: str = "Forensic_Report.pdf"):
    """
    Generates a Daubert-compliant Expert Forensic Report in PDF format.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=14,
        alignment=TA_CENTER
    )
    
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor("#2C3E50")
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 8
    normal_style.alignment = TA_JUSTIFY
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        textColor=colors.HexColor("#C0392B"),
        backColor=colors.HexColor("#F2F3F4"),
        spaceAfter=10,
        leftIndent=10,
        rightIndent=10
    )

    Story = []

    # Header
    Story.append(Paragraph("TRUTHVECTOR FORENSIC INTELLIGENCE", title_style))
    Story.append(Paragraph("Expert Mathematical Stylometry & Authorship Report", styles['Heading3']))
    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=1, spaceAfter=1, hAlign='CENTER', vAlign='BOTTOM', dash=None))
    Story.append(Spacer(1, 12))

    # Document Metadata (Chain of Custody)
    Story.append(Paragraph("1. CHAIN OF CUSTODY (DAUBERT COMPLIANCE)", h2_style))
    Story.append(Paragraph("This report verifies the mathematical integrity and stylistic homogeneity of the ingested document. A cryptographic hash was generated prior to any processing to ensure evidentiary admissibility.", normal_style))
    
    meta_data = [
        ["Date of Analysis:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Filename:", doc_record.get('filename', 'Unknown')],
        ["SHA-256 Hash:", doc_record.get('sha256_hash', 'ERROR_NO_HASH')],
        ["Cleaned Length:", f"{doc_record.get('cleaned_length', 0)} characters"]
    ]
    
    t = Table(meta_data, colWidths=[120, 380])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    Story.append(t)
    Story.append(Spacer(1, 20))

    # Methodology
    Story.append(Paragraph("2. METHODOLOGY: UNIFIED DOCUMENT GRAPH (UDG)", h2_style))
    method_text = """
    This analysis utilizes a Unified Document Graph architecture via the <b>spaCy</b> NLP engine and <b>NetworkX</b>. 
    The document was compiled into a mathematical topology where tokens serve as nodes, and syntactic dependencies 
    serve as edges. Subgraph motifs were extracted to establish the author's deeply unconscious structural fingerprint. 
    Sliding textual windows were then scored using Cosine Similarity against the global baseline, producing normalized 
    Z-Scores to identify statistically significant stylistic deviations.
    """
    Story.append(Paragraph(method_text, normal_style))
    Story.append(Spacer(1, 20))

    # Anomalies
    Story.append(Paragraph("3. STATISTICALLY SIGNIFICANT ANOMALIES", h2_style))
    Story.append(Paragraph("The following textual segments mathematically deviate from the document's established structural baseline by more than 1.0 standard deviations (Z-Score). Values exceeding +3.0 strongly indicate structural forgery, heavy tampering, or a distinct secondary author.", normal_style))
    Story.append(Spacer(1, 10))

    significant_anomalies = [a for a in anomalies if a.get('z_score', 0) >= 1.0]
    
    if not significant_anomalies:
        Story.append(Paragraph("<b>CONCLUSION:</b> No statistically significant anomalies were detected. The document appears structurally homogeneous.", normal_style))
    else:
        for i, anomaly in enumerate(significant_anomalies):
            Story.append(Paragraph(f"Anomaly #{i+1}: {anomaly['range']}", styles['Heading4']))
            Story.append(Paragraph(f"<b>Z-Score:</b> +{anomaly['z_score']:.2f} Standard Deviations", normal_style))
            
            # Format the snippet nicely
            preview = anomaly['preview']
            if len(preview) > 300:
                preview = preview[:300] + "..."
            
            Story.append(Paragraph(f"<i>Extracted Text Snippet:</i>", normal_style))
            Story.append(Paragraph(preview, code_style))
            Story.append(Spacer(1, 15))

    # Build PDF
    doc.build(Story)
    return output_path

if __name__ == "__main__":
    # Test execution
    dummy_doc = {
        'filename': 'Test_Contract_001.pdf',
        'sha256_hash': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        'cleaned_length': 4500
    }
    dummy_anomalies = [
        {'range': 'Sentences 12 to 15', 'z_score': 3.42, 'preview': 'The company shall not be held liable for any damages resulting from...'},
        {'range': 'Sentences 40 to 42', 'z_score': 1.15, 'preview': 'Payment must be rendered within 30 days of the invoice date...'}
    ]
    
    generate_forensic_report(dummy_doc, dummy_anomalies, "Test_Report.pdf")
    print("Test report generated at Test_Report.pdf")
