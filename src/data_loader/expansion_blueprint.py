"""
FORENSIC ANTIQUITY ENGINE - EXPANSION BLUEPRINT
Refactored to use the unified CorpusIngestionEngine.
"""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.data_loader.corpus_engine import (
    CorpusIngestionEngine,
    ConlluParser,
    TeiXmlParser,
    CalTextParser,
    MandaicTextParser,
    TitusHtmlParser,
    ParserStrategy
)

class OraccJsonParser(ParserStrategy):
    """
    Parses ORACC Cuneiform JSON formats (e.g. Gilgamesh / Baal Cycle).
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        import json
        words = []
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            return words

        def extract_words(node):
            if node.get('node') == 'w':
                lemma = node.get('cf', node.get('form', ''))
                pos = node.get('pos', 'u')
                form = node.get('form', '')
                if lemma:
                    words.append(("unknown", self.source_name, form, lemma, pos))
            if 'cdl' in node:
                for child in node['cdl']:
                    extract_words(child)

        text_node = data.get('text', {})
        extract_words(text_node)
        return words

class QuranXmlParser(ParserStrategy):
    """
    Parses Quranic Arabic Corpus XML.
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        import xml.etree.ElementTree as ET
        words = []
        try:
            root = ET.fromstring(text_content)
            for sura in root.findall('.//sura'):
                sura_id = sura.get('id')
                for aya in sura.findall('.//aya'):
                    aya_id = aya.get('id')
                    verse_id = f"{sura_id}:{aya_id}"
                    for word in aya.findall('.//word'):
                        form = word.get('form', '')
                        lemma = word.get('lemma', form)
                        pos = word.get('pos', 'U')
                        words.append((verse_id, self.source_name, form, lemma, pos))
        except ET.ParseError:
            pass
        return words

def run_legacy_expansions():
    # 1. Gospel of Thomas (CONLL-U)
    coptic_engine = CorpusIngestionEngine("coptic.db")
    mock_thomas = '''# sent_id = thomas.1
1	ⲡⲉϫⲉ	ⲡⲉϫⲉ	VERB	VBD	_	0	root	_	_
2	ⲓⲏⲥⲟⲩⲥ	ⲓⲏⲥⲟⲩⲥ	PROPN	NNP	_	1	nsubj	_	_
'''
    coptic_engine.ingest(
        source_url="https://raw.githubusercontent.com/CopticScriptorium/corpora/master/besa-letters/besa.letters.conllu",
        strategy=ConlluParser("THOMAS"),
        source_name="THOMAS",
        fallback_data=mock_thomas
    )

    # 2. Quranic Corpus (XML)
    arabic_engine = CorpusIngestionEngine("arabic.db")
    mock_quran = '''<?xml version="1.0" encoding="UTF-8"?>
    <quran><sura id="1"><aya id="1"><word id="1" form="بِسْمِ" lemma="ٱسْم" pos="N" /></aya></sura></quran>'''
    arabic_engine.ingest(
        source_url="http://corpus.quran.com/download/quranic-corpus-morphology-0.4.xml",
        strategy=QuranXmlParser("QURAN"),
        source_name="QURAN",
        fallback_data=mock_quran
    )

    # 3. Ugaritic Baal Cycle / Gilgamesh (ORACC JSON)
    cuneiform_engine = CorpusIngestionEngine("cuneiform.db")
    mock_oracc = '{"text": {"cdl": [{"node": "w", "form": "a-wa-tu", "cf": "awatu", "pos": "N"}]}}'
    cuneiform_engine.ingest(
        source_url="http://oracc.museum.upenn.edu/cams/gkab/corpusjson/Q000039.json",
        strategy=OraccJsonParser("GILG"),
        source_name="GILG",
        fallback_data=mock_oracc
    )

if __name__ == "__main__":
    print("Executing Refactored Expansion Blueprint via Corpus Ingestion Engine...")
    run_legacy_expansions()
    
    # Example of Phase 2 execution
    gnostic_engine = CorpusIngestionEngine("gnostic_expansions.db")
    gnostic_engine.ingest(
        source_url="http://mock-mandaic-source.org/ginza_rabba.txt",
        strategy=MandaicTextParser("GINZA_RABBA"),
        source_name="GINZA_RABBA",
        fallback_data="mandaic_word_1 mandaic_word_2"
    )
