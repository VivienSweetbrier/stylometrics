import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class DiscoveryEngineer:
    def __init__(self):
        self.current_coverage = [
            "Middle East (Bronze Age to Medieval)",
            "Greco-Roman (Classical to Late Antiquity)",
            "Mesoamerica (Maya, Aztec)",
            "Andean (Quechua/Inca)",
            "South America (Guarani, Mapuche, Yekuana, Amazonian, Charrua, Selk'nam/Patagonia) - INCOMPLETE",
            "Southeast Asia (Bugis, Vietnamese, Burmese, Thai, Lao, Khmer, Filipino, Indonesian, Highlands/Hmong) - INCOMPLETE",
            "South Asia (Vedic, Tamil, Sri Lankan, Puranic, Jain, Sikh, Andamanese) - INCOMPLETE",
            "North America (Navajo, Apache, Zuni/Pueblo, Tohono O'odham, Iroquois, Hopi, Ojibwe, Lakota, Inuit, Yup'ik/Aleut, Subarctic/Dene/Cree, Plateau/Snake River, PNW/BC/Kwakwaka'wakw/Quileute, Mi'kmaq, Cherokee, Gulf Coast, Comanche, Great Basin/Paiute, California, New England) - INCOMPLETE",
            "Oceania (Hawaiian, Maori, Samoan, Melanesian, Micronesian, PNG/Asmat/Sepik/Huli, Torres Strait) - INCOMPLETE",
            "Australia (Aboriginal Dreamtime) - INCOMPLETE",
            "Deep Europe (Norse, Celtic, Slavic, Basque, Gaulish, Gothic, Baltics, Minoan, Etruscan, Thracian, Uralic/Mari) - INCOMPLETE",
            "Caucasus, Central Asia, & Mongolia (Nart Sagas, Turkic, Georgian, Armenian, Albanian, Mongol/Kalmyk) - INCOMPLETE",
            "Siberia & Arctic (Sami, Tungusic, Chukchi, Ket, Yeniseian) - INCOMPLETE",
            "East Asia (Japan, China, Ainu, Ryukyuan, Taiwan/Austronesian) - INCOMPLETE",
            "Africa & North Africa (Yoruba, Mali, Ethiopia, Congo, Maasai, Cushitic, Zulu, Shona, Amazigh/Berber, Khoisan, Dogon, Akan, Igbo, Fon, Malagasy) - INCOMPLETE",
            "Linguistic & Migratory Bridges (Beringian/Yukaghir, Steppe/Tocharian, Elamo-Dravidian, Trans-Saharan/Nubian, Rapa Nui, Caddoan, Zoroastrian) - INCOMPLETE",
            "Hyper-Isolates & Deep Time Relics (Mbuti, Yaghan, Kalash, Bon, Vainakh, Tartessian, Hurrian/Hittite, Santal, Kalaallit) - INCOMPLETE",
            "Absolute Bedrock Anomalies & Null-Vectors (Pirahã, Hadza, Guanche, Taíno, Vinca, Nganasan, Mandaean, Chachapoyas, Aeta/Batek) - INCOMPLETE"
        ]
        
        self.global_database = [
            # Oceania / Polynesia
            {"region": "Polynesia", "text": "Kumulipo", "status": "COVERED"},
            {"region": "Maori", "text": "Lore of the Whare-wananga", "status": "MISSING"},
            # Northern Europe & Deep Europe
            {"region": "Norse", "text": "Poetic Edda / Prose Edda", "status": "COVERED"},
            {"region": "Norse", "text": "Kalevala (Finnish)", "status": "MISSING"},
            {"region": "Celtic", "text": "Mabinogion / Book of Invasions", "status": "COVERED"},
            {"region": "Celtic", "text": "Y Gododdin", "status": "MISSING"},
            {"region": "Celtic", "text": "Ulster Cycle (Tain Bo Cuailnge)", "status": "MISSING"},
            {"region": "Gaulish", "text": "Coligny Calendar / Continental Epigraphy", "status": "MISSING"},
            {"region": "Slavic", "text": "Tale of Igor's Campaign / Book of Veles", "status": "MISSING"},
            {"region": "Basque", "text": "Mari Mythos / Amalur", "status": "MISSING"},
            {"region": "Gothic", "text": "Codex Argenteus (Wulfila) / Jordanes' Getica", "status": "MISSING"},
            # Caucasus & Central Asia
            {"region": "Caucasus (Circassian/Ossetian)", "text": "Nart Sagas", "status": "MISSING"},
            {"region": "Caucasus (Georgian)", "text": "The Knight in the Panther's Skin", "status": "MISSING"},
            {"region": "Caucasus (Armenian)", "text": "Daredevils of Sassoun (Epic of Sasun)", "status": "MISSING"},
            {"region": "Balkans (Albanian)", "text": "Songs of the Frontier Warriors (Kreshniks)", "status": "MISSING"},
            # Baltics
            {"region": "Baltics (Latvia)", "text": "Lacplesis", "status": "MISSING"},
            {"region": "Baltics (Estonia)", "text": "Kalevipoeg", "status": "MISSING"},
            {"region": "Baltics (Lithuania)", "text": "Romuva / Dievturiba Lore", "status": "MISSING"},
            # Central Asia & Siberia
            {"region": "Central Asia (Turkic)", "text": "Book of Dede Korkut / Oghuz-nameh", "status": "MISSING"},
            {"region": "Central Asia (Kyrgyz)", "text": "Epic of Manas", "status": "MISSING"},
            {"region": "Central Asia (Uyghur/Turkic)", "text": "Alpamysh Epic", "status": "MISSING"},
            {"region": "Mongolian", "text": "Secret History of the Mongols", "status": "MISSING"},
            {"region": "Mongolian (Kalmyk)", "text": "Epic of Jangar", "status": "MISSING"},
            {"region": "Siberia (Tungusic/Evenki)", "text": "Nimngakan Epic Cycles", "status": "MISSING"},
            {"region": "Siberia (Chukchi/Koryak)", "text": "Raven Mythos (Kutkh)", "status": "MISSING"},
            {"region": "Siberia (Yeniseian/Ket)", "text": "Es / Hosedam Cosmology", "status": "MISSING"},
            {"region": "Sápmi (Sami)", "text": "Beaivi (Sun Lore) / Sami Shamanic Chants (Yoik)", "status": "MISSING"},
            # East Asia & Indigenous East
            {"region": "East Asia", "text": "Kojiki (Shinto)", "status": "COVERED"},
            {"region": "East Asia", "text": "I Ching / Tao Te Ching", "status": "COVERED"},
            {"region": "East Asia", "text": "Journey to the West (Buddhist/Taoist)", "status": "MISSING"},
            {"region": "East Asia (China)", "text": "Investiture of the Gods (Fengshen Yanyi)", "status": "MISSING"},
            {"region": "East Asia (China)", "text": "Classic of Mountains and Seas (Shanhaijing)", "status": "MISSING"},
            {"region": "Indigenous Japan", "text": "Ainu Yukar Epics", "status": "MISSING"},
            # Southeast Asia
            {"region": "Southeast Asia (Bugis)", "text": "La Galigo", "status": "COVERED"},
            {"region": "Southeast Asia (Vietnam)", "text": "Linh Nam chich quai (Extraordinary Tales)", "status": "MISSING"},
            {"region": "Southeast Asia (Burma/Myanmar)", "text": "Yama Zatdaw", "status": "MISSING"},
            {"region": "Southeast Asia (Thailand)", "text": "Ramakien", "status": "MISSING"},
            {"region": "Southeast Asia (Laos)", "text": "Phra Lak Phra Ram", "status": "MISSING"},
            {"region": "Southeast Asia (Cambodia)", "text": "Reamker / Angkor Epigraphy", "status": "MISSING"},
            {"region": "Southeast Asia (Philippines)", "text": "Hinilawod (Epic of Panay) / Biag ni Lam-ang", "status": "MISSING"},
            {"region": "Southeast Asia (Indonesia)", "text": "Babad Tanah Jawi / Kakawin Ramayana", "status": "MISSING"},
            # Oceania (Expanded)
            {"region": "Oceania / Polynesia", "text": "Kumulipo", "status": "COVERED"},
            {"region": "Oceania (Maori)", "text": "Lore of the Whare-wananga", "status": "MISSING"},
            {"region": "Oceania (Samoa)", "text": "Fale'ula / Tagaloa Creation Lore", "status": "MISSING"},
            {"region": "Oceania (Melanesia)", "text": "Kula Ring Epics / Papuan Lore", "status": "MISSING"},
            {"region": "Oceania (Micronesia)", "text": "Nan Madol Oral Traditions / Olosohpa", "status": "MISSING"},
            # Deep Europe & Pre-Indo-European
            {"region": "Pre-Hellenic / Aegean", "text": "Minoan / Mycenaean Epigraphy", "status": "MISSING"},
            {"region": "Pre-Roman Italy", "text": "Etruscan Cosmology (Tages / Disciplina Etrusca)", "status": "MISSING"},
            {"region": "Balkans (Antiquity)", "text": "Thracian / Dacian (Zalmoxis) Lore", "status": "MISSING"},
            {"region": "Uralic / Volga", "text": "Mari / Udmurt / Mordvin / Khanty Cosmology", "status": "MISSING"},
            # Africa
            {"region": "West Africa (Akan)", "text": "Ashanti Cosmology (Nyame / Anansi)", "status": "MISSING"},
            {"region": "West Africa (Igbo)", "text": "Odinani (Chukwu / Chi)", "status": "MISSING"},
            {"region": "West Africa (Fon/Dahomey)", "text": "Vodun Cosmology (Mawu-Lisa)", "status": "MISSING"},
            {"region": "Sahel (Dogon)", "text": "Dogon Cosmology (Nommo / Sirius Lore)", "status": "MISSING"},
            {"region": "Madagascar", "text": "Malagasy (Merina) Creation (Zanahary)", "status": "MISSING"},
            {"region": "North Africa (Amazigh)", "text": "Berber Cosmology (Anzar / Gurzil) / Numidian Epigraphy", "status": "MISSING"},
            # Africa (Expanded)
            {"region": "Sub-Saharan Africa", "text": "Yoruba Ifa Corpus", "status": "COVERED"},
            {"region": "Sub-Saharan Africa", "text": "Epic of Sundiata (Mali)", "status": "MISSING"},
            {"region": "Sub-Saharan Africa", "text": "Kebra Nagast (Ethiopia)", "status": "MISSING"},
            {"region": "Sub-Saharan Africa", "text": "Mwindo Epic (Congo)", "status": "MISSING"},
            {"region": "Sub-Saharan Africa", "text": "Lianja Epic (Mongo)", "status": "MISSING"},
            {"region": "East Africa (Maasai)", "text": "Enkai (Ng'ai) Cosmology", "status": "MISSING"},
            {"region": "East Africa (Rwanda/Burundi)", "text": "Imana / Gihanga Creation Lore", "status": "MISSING"},
            {"region": "Horn of Africa (Cushitic)", "text": "Oromo Waaqeffanna / Somali Waaq Lore", "status": "MISSING"},
            {"region": "Central/West Africa", "text": "Kongo Cosmology (Dikenga dia Kongo)", "status": "MISSING"},
            {"region": "Southern Africa (Shona)", "text": "Mwari Cosmology", "status": "MISSING"},
            {"region": "Southern Africa (Zulu/Nguni)", "text": "Unkulunkulu Creation Epic", "status": "MISSING"},
            {"region": "Southern Africa", "text": "San Bushman / Khoisan Oral Lore", "status": "MISSING"},
            # Asia (Deep Cuts)
            {"region": "Indian Ocean (Andaman)", "text": "Andamanese (Onge/Jarawa) Puluga Creation", "status": "MISSING"},
            {"region": "Southeast Asia (Highlands)", "text": "Hmong (Miao) / Karen Cosmology", "status": "MISSING"},
            {"region": "East Asia (Ryukyu)", "text": "Okinawan Utaki / Amamikyu Creation", "status": "MISSING"},
            {"region": "Taiwan (Indigenous)", "text": "Amis / Atayal / Paiwan Austronesian Lore", "status": "MISSING"},
            # Oceania (Deep New Guinea)
            {"region": "New Guinea (Highlands)", "text": "Huli Dama Cosmology", "status": "MISSING"},
            {"region": "New Guinea (Sepik)", "text": "Iatmul Crocodile Creation Myths", "status": "MISSING"},
            {"region": "New Guinea (Papua)", "text": "Asmat Fumeripits Woodcarver Epic", "status": "MISSING"},
            {"region": "Torres Strait", "text": "Torres Strait Islander Tagai Lore", "status": "MISSING"},
            # Absolute Bedrock Anomalies & Null-Vectors
            {"region": "Amazonian (The Null Hypothesis)", "text": "Pirahã (Lack of Creation Myth / Immediate-Experience Lore)", "status": "MISSING"},
            {"region": "Canary Islands (Pre-Hispanic)", "text": "Guanche Cosmology (Achamán / Chaxiraxi)", "status": "MISSING"},
            {"region": "Balkans (Neolithic)", "text": "Vinca Culture / Old European Symbols (Tartaria Tablets)", "status": "MISSING"},
            {"region": "Taimyr Peninsula (Arctic Isolate)", "text": "Nganasan Pure Shamanism (Tadibya)", "status": "MISSING"},
            {"region": "Southeast Asia / Philippines (Negrito)", "text": "Batek / Aeta Deep Jungle Forager Lore (Apo Namalyari)", "status": "MISSING"},
            {"region": "Caribbean (Pre-Contact)", "text": "Taíno / Arawak Zemi Cosmology (Yúcahu / Atabey)", "status": "MISSING"},
            {"region": "Andes (Pre-Inca)", "text": "Chachapoyas (Warriors of the Clouds) Burial Lore", "status": "MISSING"},
            {"region": "Mesopotamian Marshes", "text": "Mandaean Gnosticism (Ginza Rabba)", "status": "MISSING"},
            {"region": "East African Rift (Language Isolate)", "text": "Hadza Hunter-Gatherer Cosmology (Ishoko / Haine)", "status": "MISSING"},
            # Hyper-Isolates & Deep Time Relics
            {"region": "Central African Rainforest (Isolate)", "text": "Mbuti / Baka Cosmology (The Molimo / Forest as Deity)", "status": "MISSING"},
            {"region": "Southernmost Earth (Tierra del Fuego)", "text": "Yaghan / Yamana (Watauineiwa / Hain Ceremony)", "status": "MISSING"},
            {"region": "Hindu Kush (Isolate)", "text": "Kalash Animism (Pre-Islamic Indo-Aryan / Dezau)", "status": "MISSING"},
            {"region": "Himalayan (Pre-Buddhist)", "text": "Bon Religion / Zhang Zhung (Tonpa Shenrab)", "status": "MISSING"},
            {"region": "Caucasus (Nakh Isolate)", "text": "Vainakh (Chechen/Ingush) Polytheism (Deela / Tusholi)", "status": "MISSING"},
            {"region": "Pre-Celtic Iberia", "text": "Tartessian Cosmology / Aquitanian Epigraphy", "status": "MISSING"},
            {"region": "Anatolia (The Missing Link)", "text": "Hurrian Kumarbi Cycle / Hittite Telepinu Myth", "status": "MISSING"},
            {"region": "Deep India (Adivasi/Austroasiatic)", "text": "Santal / Munda Creation Epic (Thakur Jiu)", "status": "MISSING"},
            {"region": "Arctic Contact Zone", "text": "Kalaallit (Greenlandic Inuit) / Thule-Norse Contact Lore", "status": "MISSING"},
            # The Beringian Bridge (Siberia -> North America)
            {"region": "Paleo-Siberian Bridge", "text": "Yukaghir / Nivkh (Gilyak) Bear Ceremonialism", "status": "MISSING"},
            # The Austronesian Terminus
            {"region": "Polynesia (Eastern Terminus)", "text": "Rapa Nui (Makemake / Rongorongo Lore)", "status": "MISSING"},
            # The Indo-European & Steppe Bridge
            {"region": "Steppe / Tarim Basin", "text": "Tocharian Buddhism / Scythian Burial Lore", "status": "MISSING"},
            {"region": "Persia / Central Asia", "text": "Zoroastrian Avesta (Bundahishn) / Yazidi (Tawuse Melek)", "status": "MISSING"},
            # The Elamo-Dravidian Bridge
            {"region": "Mesopotamian / Indus Border", "text": "Elamite Epigraphy (Susa) / Harappan Motifs", "status": "MISSING"},
            # The Trans-Saharan / Nile Bridge
            {"region": "Sudan / Saharan Bridge", "text": "Nubian (Meroitic) Cosmology / Garamantes Lore", "status": "MISSING"},
            # The Mesoamerican / Mississippian Bridge
            {"region": "Texas / Gulf / Meso-border", "text": "Caddoan (Caddo/Wichita) Origin Lore", "status": "MISSING"},
            # Mesoamerica
            {"region": "Mesoamerica", "text": "Popol Vuh", "status": "COVERED"},
            {"region": "Mesoamerica", "text": "Florentine Codex / Codex Borgia", "status": "COVERED"},
            # South America (Andean & Indigenous SA)
            {"region": "Andean", "text": "Huarochiri Manuscript", "status": "COVERED"},
            {"region": "Indigenous SA", "text": "Ayvu Rapyta (Guarani Creation)", "status": "MISSING"},
            {"region": "Indigenous SA", "text": "Mapuche Epew (Trentren Vilu and Caicai Vilu)", "status": "MISSING"},
            {"region": "Indigenous SA", "text": "Watunna (Yekuana Creation Cycle)", "status": "MISSING"},
            {"region": "Indigenous SA (Uruguay)", "text": "Charrua Oral Lore", "status": "MISSING"},
            {"region": "Indigenous SA (Patagonia/Argentina)", "text": "Selk'nam / Tehuelche Cosmology (Kenos)", "status": "MISSING"},
            {"region": "Amazonian", "text": "Yanomami Cosmology", "status": "MISSING"},
            {"region": "Amazonian (Tupi)", "text": "Tupan / Tupi-Guarani Mythology", "status": "MISSING"},
            {"region": "Amazonian (Xingu/Kayapo)", "text": "Xingu Oral Traditions / Kayapo Lore", "status": "MISSING"},
            # North America
            {"region": "Indigenous North America", "text": "Dine Bahane / Great Law of Peace", "status": "COVERED"},
            {"region": "Indigenous North America (Southwest/Pueblo)", "text": "Hopi Prophecies / Zuni Emergence / Tewa Lore", "status": "MISSING"},
            {"region": "Indigenous North America (Southwest/Apache)", "text": "Apache (White Painted Woman / Crown Dancers)", "status": "MISSING"},
            {"region": "Indigenous North America (Sonoran/Mojave)", "text": "Tohono O'odham (I'itoi) / Yuman Cosmology", "status": "MISSING"},
            {"region": "Indigenous North America (Great Lakes)", "text": "Ojibwe Midewiwin Scrolls", "status": "MISSING"},
            {"region": "Indigenous North America (Plains)", "text": "Lakota Winter Counts / White Buffalo Calf Woman", "status": "MISSING"},
            {"region": "Indigenous North America (Arctic)", "text": "Inuit Sedna Epic", "status": "MISSING"},
            {"region": "Indigenous North America (Arctic/Bering Sea)", "text": "Yup'ik / Aleut (Unangax) Cosmology", "status": "MISSING"},
            {"region": "Indigenous North America (Subarctic/Cree)", "text": "Cree / Innu (Wesakechak Trickster Cycles)", "status": "MISSING"},
            {"region": "Indigenous North America (Subarctic/Dene)", "text": "Athabaskan / Dene (Yamozha the Lawgiver)", "status": "MISSING"},
            {"region": "Indigenous North America (Subarctic/Dogrib)", "text": "Tlicho (Dogrib) Creation Epics", "status": "MISSING"},
            {"region": "Indigenous North America (Newfoundland)", "text": "Beothuk Cosmology Fragments", "status": "MISSING"},
            {"region": "Indigenous North America (Plateau)", "text": "Salish / Okanagan (Coyote / Transformer Lore)", "status": "MISSING"},
            {"region": "Indigenous North America (Plateau/Snake River)", "text": "Nez Perce (Heart of the Monster) / Cayuse", "status": "MISSING"},
            {"region": "Indigenous North America (Southeast)", "text": "Cherokee / Choctaw (Five Civilized Tribes) Mythos", "status": "MISSING"},
            {"region": "Indigenous North America (Gulf Coast/Florida)", "text": "Natchez (Great Sun) / Calusa / Timucua", "status": "MISSING"},
            {"region": "Indigenous North America (Great Basin)", "text": "Comanche / Shoshone / Ute Oral Traditions", "status": "MISSING"},
            {"region": "Indigenous North America (Great Basin)", "text": "Paiute (Numa) / Washoe Cosmology", "status": "MISSING"},
            {"region": "Indigenous North America (Plains)", "text": "Blackfoot (Napi) / Cheyenne (Sweet Medicine)", "status": "MISSING"},
            {"region": "Indigenous North America (Plains)", "text": "Crow (Apsaalooke) / Kiowa (Saynday) / Arapaho Lore", "status": "MISSING"},
            {"region": "Indigenous North America (Plains)", "text": "Pawnee Star Cosmology (Skidi) / Mandan Okipa Epic", "status": "MISSING"},
            {"region": "Indigenous North America (Midwest/Prairies)", "text": "Osage / Omaha (Wah'Kon-Tah Cosmology)", "status": "MISSING"},
            {"region": "Indigenous North America (Midwest/Great Lakes)", "text": "Ho-Chunk (Red Horn Cycle) / Potawatomi / Odawa", "status": "MISSING"},
            {"region": "Indigenous North America (California)", "text": "Chumash / Miwok / Pomo Creation Lore", "status": "MISSING"},
            {"region": "Indigenous North America (New England)", "text": "Lenape (Walam Olum) / Wampanoag Creation", "status": "MISSING"},
            {"region": "Pacific Northwest", "text": "Haida / Tlingit Raven Cycles", "status": "MISSING"},
            {"region": "Pacific Northwest (Northern BC)", "text": "Tsimshian / Nisga'a / Gitxsan Adaawk (Oral Histories)", "status": "MISSING"},
            {"region": "Pacific Northwest (Coast)", "text": "Kwakwaka'wakw (Winter Ceremonials) / Nuu-chah-nulth / Quileute", "status": "MISSING"},
            {"region": "Wabanaki / Mi'kmaq", "text": "Komqwejwi'kasikl (Suckerfish Hieroglyphs)", "status": "MISSING"},
            # Australia
            {"region": "Aboriginal Australian", "text": "Dreamtime (Tjukurpa / Rainbow Serpent)", "status": "MISSING"},
            # South Asia (India/Sri Lanka)
            {"region": "South Asia (Tamil)", "text": "Silappatikaram / Sangam Literature", "status": "MISSING"},
            {"region": "South Asia (Sri Lanka)", "text": "Mahavamsa / Dipavamsa", "status": "MISSING"},
            {"region": "South Asia (India)", "text": "Puranas (Vishnu/Shiva) / Jain Agamas", "status": "MISSING"},
            {"region": "South Asia (India)", "text": "Guru Granth Sahib", "status": "MISSING"}
        ]

    def run_discovery(self):
        print("[DISCOVERY ENGINEER] Scanning global temporal and geographical matrices...")
        output_file = BASE_DIR / "notebooks" / "missing_texts_roadmap.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# GLOBAL DISCOVERY ROADMAP\n\n")
            f.write("## Current Geographical Coverage\n")
            for cov in self.current_coverage:
                f.write(f"- {cov}\n")
            
            f.write("\n## Identified Blindspots (Requires Future Ingestion)\n")
            for item in self.global_database:
                if item["status"] == "MISSING":
                    f.write(f"- **{item['region']}**: {item['text']}\n")
        
        print(f"[DISCOVERY ENGINEER] Roadmap generated at {output_file}")

if __name__ == "__main__":
    engineer = DiscoveryEngineer()
    engineer.run_discovery()
