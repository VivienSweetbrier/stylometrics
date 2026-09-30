import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OntologyDocument:
    source_id: str
    title: str
    author: str
    chunks: List[DocumentChunk] = field(default_factory=list)

def parse_federalist_papers(file_path: Path) -> OntologyDocument:
    text = file_path.read_text(encoding="utf-8-sig")
    
    # Structural marker: THE FEDERALIST.\nNo. [ROMAN NUMERAL]
    # We'll split the text using this pattern
    pattern = re.compile(r'THE FEDERALIST\.\s*\nNo\.\s*([IVXLC]+)', re.IGNORECASE)
    parts = pattern.split(text)
    
    doc = OntologyDocument(
        source_id="federalist_papers",
        title="The Federalist Papers",
        author="Alexander Hamilton, James Madison, John Jay"
    )
    
    # parts[0] is everything before No. I (Title, TOC, etc.)
    # parts[1] is 'I', parts[2] is content of I, parts[3] is 'II', parts[4] is content of II, etc.
    for i in range(1, len(parts), 2):
        paper_num = parts[i]
        content = parts[i+1].strip()
        
        # Clean up Gutenberg footer from the last paper
        if i == len(parts) - 2:
            footer_idx = content.find("*** END OF THE PROJECT GUTENBERG EBOOK")
            if footer_idx != -1:
                content = content[:footer_idx].strip()
        
        chunk = DocumentChunk(
            chunk_id=f"federalist_no_{paper_num}",
            content=content,
            metadata={"paper_number": paper_num}
        )
        doc.chunks.append(chunk)
        
    return doc

def parse_bixby_letter(file_path: Path) -> OntologyDocument:
    text = file_path.read_text(encoding="utf-8")
    
    # Structural markers:
    # Header usually contains date and location.
    # Salutation: "Dear Madam,"
    # Sign-off: "Yours, ..."
    
    salutation_idx = text.find("Dear Madam,")
    signoff_idx = text.rfind("Yours,")
    
    header = text[:salutation_idx].strip()
    body = text[salutation_idx:signoff_idx].strip()
    signoff = text[signoff_idx:].strip()
    
    chunk = DocumentChunk(
        chunk_id="bixby_letter_main",
        content=body,
        metadata={
            "header": header,
            "signoff": signoff
        }
    )
    
    return OntologyDocument(
        source_id="bixby_letter",
        title="Letter to Mrs. Bixby",
        author="Abraham Lincoln",
        chunks=[chunk]
    )

def parse_qanon_drops(file_path: Path) -> OntologyDocument:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    
    doc = OntologyDocument(
        source_id="qanon_drops",
        title="QAnon Forum Drops",
        author="Q"
    )
    
    for drop in data:
        # Structural markers are implicit in JSON keys
        chunk = DocumentChunk(
            chunk_id=f"drop_{drop['drop_id']}",
            content=drop['text'],
            metadata={
                "timestamp": drop['timestamp'],
                "tripcode": drop.get('tripcode', '')
            }
        )
        doc.chunks.append(chunk)
        
    return doc

if __name__ == "__main__":
    base_dir = Path(r"c:\Users\Vivian\Desktop\Synoptics\data\raw\historical_corpus")
    
    fed_doc = parse_federalist_papers(base_dir / "federalist_papers.txt")
    print(f"Parsed {fed_doc.title}: {len(fed_doc.chunks)} papers found.")
    
    bixby_doc = parse_bixby_letter(base_dir / "bixby_letter.txt")
    print(f"Parsed {bixby_doc.title}: {len(bixby_doc.chunks)} chunks found.")
    
    q_doc = parse_qanon_drops(base_dir / "qanon_drops.json")
    print(f"Parsed {q_doc.title}: {len(q_doc.chunks)} drops found.")
