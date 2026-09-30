import hashlib
import os
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

class LegalDocumentIngestor:
    def __init__(self, strip_bates=True):
        self.strip_bates = strip_bates
        
    def _generate_file_hash(self, file_path: Path) -> str:
        """
        Generates a SHA-256 hash of the RAW BINARY FILE. 
        Crucial for the Daubert standard Chain of Custody.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _clean_legal_text(self, text: str) -> str:
        """
        Removes common noise from legal documents (Bates numbers, excessive whitespace, page headers).
        Processed safely line-by-line to prevent Regex memory explosions.
        """
        bates_pattern = re.compile(r'\b(BATES|DEF|PLTF|CONFIDENTIAL)[\s\-]*\d{3,9}\b', flags=re.IGNORECASE)
        whitespace_pattern = re.compile(r'[ \t]+')
        
        cleaned_lines = []
        last_was_empty = False
        
        import io
        for line in io.StringIO(text):
            line = line.strip('\n')
            if self.strip_bates:
                line = bates_pattern.sub('', line)
                
            line = whitespace_pattern.sub(' ', line).strip()
            
            is_empty = (line == "")
            if is_empty and last_was_empty:
                continue
                
            last_was_empty = is_empty
            cleaned_lines.append(line)
            
        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()
            
        return '\n'.join(cleaned_lines)

    def _extract_pdf(self, file_path: Path):
        if fitz is None:
            raise ImportError("PyMuPDF is not installed. Run `pip install pymupdf`")
        
        doc = fitz.open(file_path)
        for page in doc:
            yield page.get_text("text")

    def _extract_docx(self, file_path: Path):
        if docx is None:
            raise ImportError("python-docx is not installed. Run `pip install python-docx`")
            
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            yield paragraph.text + "\n"
        
    def _extract_txt(self, file_path: Path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                yield line

    def ingest(self, file_path: str) -> dict:
        """
        Main entry point. Takes a file path, calculates the forensic hash, 
        extracts the text based on file type, and cleans it.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_hash = self._generate_file_hash(path)
        ext = path.suffix.lower()
        
        if ext == ".pdf":
            chunks = self._extract_pdf(path)
        elif ext == ".docx":
            chunks = self._extract_docx(path)
        elif ext == ".txt":
            chunks = self._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
        bates_pattern = re.compile(r'\b(BATES|DEF|PLTF|CONFIDENTIAL)[\s\-]*\d{3,9}\b', flags=re.IGNORECASE)
        whitespace_pattern = re.compile(r'[ \t]+')
        
        raw_length = 0
        cleaned_lines = []
        last_was_empty = False
        
        for chunk in chunks:
            raw_length += len(chunk)
            
            for line in chunk.split('\n'):
                line = line.strip('\r')
                if self.strip_bates:
                    line = bates_pattern.sub('', line)
                line = whitespace_pattern.sub(' ', line).strip()
                
                is_empty = (line == "")
                if is_empty and last_was_empty:
                    continue
                    
                last_was_empty = is_empty
                cleaned_lines.append(line)
                
        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()
            
        cleaned_text = '\n'.join(cleaned_lines)
        
        return {
            "filename": path.name,
            "sha256_hash": file_hash,
            "raw_length": raw_length,
            "cleaned_length": len(cleaned_text),
            "text": cleaned_text
        }

if __name__ == "__main__":
    # Create a dummy txt file to test the ingestor if no real docs exist
    test_file = Path("dummy_legal_doc.txt")
    if not test_file.exists():
        test_file.write_text("CONFIDENTIAL-00142\nThis is a test legal document. \n\n\nIt contains a BATES 123456 stamp.")
        
    print("="*60)
    print("LEGAL DOCUMENT INGESTION ENGINE (CHAIN OF CUSTODY)")
    print("="*60)
    
    ingestor = LegalDocumentIngestor()
    try:
        record = ingestor.ingest(str(test_file))
        print(f"File Processed : {record['filename']}")
        print(f"SHA-256 Hash   : {record['sha256_hash']} (Court Admissible Chain of Custody)")
        print(f"Raw Length     : {record['raw_length']} characters")
        print(f"Cleaned Length : {record['cleaned_length']} characters")
        print(f"\n[CLEANED TEXT PREVIEW]\n{record['text']}")
    except Exception as e:
        print(f"Error: {e}")
