import os
import re
import requests
from pathlib import Path
import traceback

class OntologyEngineer:
    """Phase 2: Ontology Engineering - Universal Data Structures"""
    @staticmethod
    def parse_gutenberg_txt(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        segments = re.split(r'(?i)\b(?:SCENE|ACT)\s+[IVXLC]+\b', text)
        valid_segments = [seg.strip() for seg in segments if len(seg.split()) > 50]
        if not valid_segments:
            raise ValueError("No valid SCENE or ACT segments found.")
        return {"format": "plaintext", "segments_count": len(valid_segments), "sample": valid_segments[0][:200]}
        
    @staticmethod
    def parse_macula_tsv(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            header = f.readline()
            if '\t' not in header:
                raise ValueError("Invalid TSV: Missing tab delimiters.")
            sample = f.readline().strip()
        return {"format": "tsv_morphology", "segments_count": "dynamic", "sample": sample}
        
    @staticmethod
    def parse_perseus_xml(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)
            if '<?xml' not in content and '<treebank' not in content:
        return {"format": "xml_treebank", "segments_count": "dynamic", "sample": content[:200]}

    # =========================================================================
    # NEW ONTOLOGY EXTENSIONS: CLASSICAL, HISTORICAL, AND MODERN
    # =========================================================================
    
    @staticmethod
    def parse_medieval_verse(filepath):
        """Parses Old English (Beowulf) 'Fitts' or French Arthurian chapters."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
        if "Morte d'Arthur" in text or "BOOK I" in text:
            # Arthurian Legends mode (Books/Chapters)
            segments = re.split(r'(?m)^CHAPTER\s+[IVXLC]+\.?\s*', text)
            valid_segments = [seg.strip() for seg in segments if len(seg.split()) > 50]
            return {"format": "arthurian_romance", "segments_count": len(valid_segments), "sample": valid_segments[1][:200] if len(valid_segments) > 1 else ""}
        else:
            # Beowulf/Fitt mode (Roman Numerals)
            segments = re.split(r'(?m)^(?:I{1,3}|IV|V|VI{1,3}|IX|X{1,3}(?:IX|IV|V?I{0,3})?|XL|L)\.(?:\s+.*)?$', text)
            valid_segments = [seg.strip() for seg in segments if len(seg.split()) > 50]
            return {"format": "old_english_verse", "segments_count": len(valid_segments), "sample": valid_segments[1][:200] if len(valid_segments) > 1 else ""}
        
    @staticmethod
    def parse_political_essays(filepath):
        """Parses documents like the Federalist Papers or Presidential Letters."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
        if "THE FEDERALIST." in text:
            # Federalist Papers mode
            segments = re.split(r'THE FEDERALIST\.\s*\nNo\.\s*[IVXLC]+', text, flags=re.IGNORECASE)
            valid_segments = [seg.strip() for seg in segments if len(seg.split()) > 50]
            return {"format": "political_essay", "segments_count": len(valid_segments), "sample": valid_segments[1][:200] if len(valid_segments) > 1 else ""}
        else:
            # Epistolary/Letter mode (e.g. Bixby Letter)
            # Naive parse removing salutation/sign-off
            body = text
            if "Dear " in text:
                body = text[text.find("Dear "):]
            if "Yours," in body:
                body = body[:body.rfind("Yours,")]
            return {"format": "historical_letter", "segments_count": 1, "sample": body[:200]}
        
    @staticmethod
    def parse_cypherpunk_archives(filepath):
        """Parses internet-era documents like Satoshi's emails and whitepapers."""
        import email
        from email import policy
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Differentiate between Whitepaper and Email structure
        if "Abstract" in content and re.search(r'(?:\n|^)(\d+\.\s+[A-Z][^\n]+)(?:\n|$)', content):
            # Whitepaper mode
            segments = re.split(r'(?:\n|^)(\d+\.\s+[A-Z][^\n]+)(?:\n|$)', content)
            valid_segments = [seg.strip() for seg in segments if len(seg.split()) > 30]
            return {"format": "whitepaper", "segments_count": len(valid_segments), "sample": valid_segments[0][:200]}
        else:
            # Email mode
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                msg = email.message_from_file(f, policy=policy.default)
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace') if not msg.is_multipart() else ""
            return {"format": "cypherpunk_email", "segments_count": 1, "sample": body[:200]}
            
    @staticmethod
    def parse_forum_dumps(filepath):
        """Parses JSON-structured data from 4chan/8chan (QAnon Drops)."""
        import json
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            
        if isinstance(data, list) and len(data) > 0 and 'text' in data[0]:
            return {"format": "json_forum_drops", "segments_count": len(data), "sample": data[0]['text'][:200]}
        else:
            raise ValueError("JSON does not match expected forum drop schema.")

class HarnessEngineer:
    """Phase 1: Integration Layer"""
    def __init__(self):
        self.ontology = OntologyEngineer()
    def safely_ingest(self, filepath):
        """Attempts to parse a file, returning a unified Ontology structure."""
        ext = filepath.suffix.lower()
        
        # Sandbox safety check
        if filepath.stat().st_size == 0:
            raise ValueError("File is empty.")
            
        if ext == '.txt':
            # Cascade through text ontologies until one successfully parses without ValueError
            errors = []
            for parser in [self.ontology.parse_gutenberg_txt, 
                           self.ontology.parse_political_essays,
                           self.ontology.parse_cypherpunk_archives,
                           self.ontology.parse_medieval_verse]:
                try:
                    return parser(filepath)
                except Exception as e:
                    errors.append(str(e))
            raise ValueError(f"All text parsers failed: {errors}")
            
        elif ext in ['.tsv', '.csv', '.dat']:
            # For data files, we could also cascade, but for now fallback to TSV parsing or forum dumps
            try:
                return self.ontology.parse_macula_tsv(filepath)
            except:
                pass
            
            try:
                return self.ontology.parse_forum_dumps(filepath)
            except Exception as e:
                raise ValueError(f"Data parsers failed: {e}")
                
        elif ext == '.xml':
            return self.ontology.parse_perseus_xml(filepath)
            
        elif ext == '.json':
            return self.ontology.parse_forum_dumps(filepath)
            
        else:
            raise ValueError(f"Harness blocked unsupported file extension: {ext}")

class ContextAndPromptEngineer:
    """Phase 4: Local LLM Delegation Layer via Ollama"""
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
    def prompt_engineer(self, node_name, node_data):
        """Constructs a hyper-specific context prompt based on the parsed ontology."""
        system_prompt = "You are a multi-lingual Computational Linguistics Micro-Agent."
        
        prompt = f"""
        Node Name: {node_name}
        Ontology Format: {node_data['format']}
        Data Sample: {node_data.get('sample', 'N/A')}
        
        Task: 
        1. Identify the likely language or text type of this data based on the sample.
        2. Propose a specific mathematical strategy (e.g., Markov Chain on POS tags, Dependency parsing, Word-Adjacency Networks) to track stylistic anomalies for this specific format.
        Keep your response under 3 sentences.
        """
        return system_prompt, prompt
        
    def delegate_task(self, node_name, node_data):
        """Spawns an asynchronous request to the local Ollama instance."""
        sys_prompt, prompt = self.prompt_engineer(node_name, node_data)
        payload = {
            "model": self.model_name,
            "system": sys_prompt,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            # We use a short timeout to fail gracefully if Ollama is busy/unavailable
            response = requests.post(self.api_url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                return f"[Error]: Ollama returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "[Error]: Could not connect to localhost:11434. Is Ollama running?"
        except Exception as e:
            return f"[Error]: {e}"

class MacroOrchestrator:
    """Phase 3: Search Graph & Correct Path Loop with Phase 4 Delegation"""
    def __init__(self, data_directory):
        self.data_dir = Path(data_directory)
        self.harness = HarnessEngineer()
        self.llm_delegation = ContextAndPromptEngineer(model_name="llama3") 
        self.knowledge_graph = {}
        
    def execute_search_graph(self, max_llm_delegations=3):
        print(f"Starting Macro Orchestrator Search Graph on: {self.data_dir}")
        print("="*60)
        
        llm_count = 0
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                filepath = Path(root) / file
                
                # We only delegate a few times to avoid spamming the console
                should_delegate_to_llm = llm_count < max_llm_delegations
                if self.process_node(filepath, delegate=should_delegate_to_llm):
                    if should_delegate_to_llm:
                        llm_count += 1
                        
        print("="*60)
        print(f"Orchestration Complete. Successfully mapped {len(self.knowledge_graph)} nodes.")
                
    def process_node(self, filepath, delegate=False):
        print(f"\n[Node] {filepath.name}")
        success = False
        attempts = 0
        
        while not success and attempts < 1:
            try:
                result = self.harness.safely_ingest(filepath)
                print(f"  -> Status: SUCCESS (Format: {result.get('format')})")
                
                self.knowledge_graph[filepath.name] = result
                success = True
                
                # PHASE 4: OLLAMA DELEGATION
                if delegate:
                    print(f"  -> [Phase 4] Spawning Ollama Micro-Agent for Linguistic Analysis...")
                    llm_analysis = self.llm_delegation.delegate_task(filepath.name, result)
                    print(f"  -> [Ollama Agent Response]:\n     {llm_analysis}")
                
            except Exception as e:
                print(f"  -> Status: FAILED | [Correct Path]: {e}")
                if filepath.name in self.knowledge_graph:
                    del self.knowledge_graph[filepath.name]
                attempts += 1
                
        return success

if __name__ == "__main__":
    data_path = r"c:\Users\Vivian\Desktop\Synoptics\data\raw"
    orchestrator = MacroOrchestrator(data_path)
    # We will test Phase 4 Ollama Delegation on the first 3 successful nodes
    orchestrator.execute_search_graph(max_llm_delegations=3)
