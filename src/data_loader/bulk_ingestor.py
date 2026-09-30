import pandas as pd
import zipfile
import tempfile
import os

class BulkIngestor:
    def __init__(self, text_column="text"):
        """
        :param text_column: If parsing a CSV, the name of the column containing the document text.
        """
        self.text_column = text_column

    def ingest_csv(self, file_path):
        """
        Reads a CSV safely (up to 50k rows) and returns a list of dictionaries.
        """
        # Hard limit to prevent RAM OOM for massive dumps
        df = pd.read_csv(file_path, nrows=50000)
        
        if self.text_column not in df.columns:
            for col in df.columns:
                if df[col].dtype == object or df[col].dtype.name == 'string':
                    self.text_column = col
                    break
        
        if self.text_column not in df.columns:
            raise ValueError(f"Could not find a text column named '{self.text_column}'.")

        df[self.text_column] = df[self.text_column].fillna("")
        
        documents = []
        for idx, row in df.iterrows():
            doc = {
                "id": f"row_{idx}",
                "text": str(row[self.text_column])
            }
            for col in df.columns:
                if col != self.text_column:
                    doc[col] = row[col]
            documents.append(doc)
            
        return documents

    def ingest_zip(self, file_path):
        """
        Reads a ZIP file safely and returns a list of dictionaries.
        Prevents zip bombs by enforcing a max uncompressed size and file limit.
        """
        MAX_FILES = 10000
        MAX_SIZE = 500 * 1024 * 1024 # 500 MB limit
        
        documents = []
        total_size = 0
        file_count = 0
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                # Prevent zip bombs by checking limits before reading
                if zip_info.is_dir():
                    continue
                
                file_count += 1
                if file_count > MAX_FILES:
                    raise ValueError(f"Too many files in ZIP (max {MAX_FILES})")
                    
                total_size += zip_info.file_size
                if total_size > MAX_SIZE:
                    raise ValueError(f"Uncompressed ZIP size exceeds limit of {MAX_SIZE} bytes")
                
                filename = os.path.basename(zip_info.filename)
                if filename.startswith('.') or filename.startswith('__MACOSX'):
                    continue
                
                if filename.endswith(('.txt', '.md', '.json', '.log')):
                    try:
                        with zip_ref.open(zip_info) as f:
                            text = f.read().decode('utf-8')
                        documents.append({
                            "id": filename,
                            "text": text
                        })
                    except Exception:
                        pass
        return documents

    def process_file(self, file_path, file_type):
        if file_type == "csv":
            return self.ingest_csv(file_path)
        elif file_type == "zip":
            return self.ingest_zip(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
