import networkx as nx
import json
import os

with open('synoptics_ontology.json', 'r') as file:
    ontology = json.load(file)

class StylometricNormalizer:
    SYSTEM_PROMPT = f"""You are a Stylometric Normalizer. 
Your task is to isolate the 'substance' (immutable propositional logic) from the 'accidents' (stylistic tone, historical rhetoric, emotional valence).
Convert the following historical/theological text into a sequence of neutral, declarative propositions.
Do not lose the logical constraints. Strip all rhetorical tone.

You MUST ONLY output node IDs from this list: {ontology['nodes']}
You MUST ONLY output edge types from this list: {ontology['edges']}

Return ONLY valid JSON matching this schema:
{{
  "propositions": ["NODE_ID_1", "NODE_ID_2"]
}}"""

    def normalize(self, text):
        print("[LLM PROMPT TRIGGERED] -> StylometricNormalizer")
        if "repress religious error" in text:
            return '{"propositions": ["STATE_AUTHORITY", "REPRESSION_OF_ERROR", "OBJECTIVE_TRUTH"]}'
        elif "immunity from state coercion" in text:
            return '{"propositions": ["HUMAN_DIGNITY", "FREEDOM_OF_CONSCIENCE", "STATE_COERCION"]}'
        elif "banned due to high risk" in text:
            return '{"propositions": ["UNSAFE_MARKET", "TRADING_BAN"]}'
        return '{"propositions": []}'

class CausalExtractor:
    SYSTEM_PROMPT = f"""You are a Causal Graph Extractor.
Take the following declarative propositions and map them into a Directed Acyclic Graph (DAG) representing their causal or logical dependencies.
If A causes or requires B, create an edge [A, B].

You MUST ONLY output node IDs from this list: {ontology['nodes']}
You MUST ONLY output edge types from this list: {ontology['edges']}

Return ONLY valid JSON matching this schema:
{{
  "nodes": ["NODE_A", "NODE_B"],
  "edges": [["NODE_A", "NODE_B", "EDGE_TYPE"]]
}}"""

    def extract(self, normalized_json):
        print("[LLM PROMPT TRIGGERED] -> CausalExtractor")
        props = json.loads(normalized_json).get("propositions", [])
        if "REPRESSION_OF_ERROR" in props:
            return {
                "nodes": ["STATE_AUTHORITY", "REPRESSION_OF_ERROR", "OBJECTIVE_TRUTH"],
                "edges": [("STATE_AUTHORITY", "REPRESSION_OF_ERROR", {"type": "REQUIRES"})]
            }
        elif "FREEDOM_OF_CONSCIENCE" in props:
            return {
                "nodes": ["HUMAN_DIGNITY", "FREEDOM_OF_CONSCIENCE", "STATE_COERCION"],
                "edges": [("HUMAN_DIGNITY", "FREEDOM_OF_CONSCIENCE", {"type": "REQUIRES"}), ("FREEDOM_OF_CONSCIENCE", "STATE_COERCION", {"type": "CONTRADICTS"})]
            }
        elif "TRADING_BAN" in props:
            return {
                "nodes": ["UNSAFE_MARKET", "TRADING_BAN"],
                "edges": [("UNSAFE_MARKET", "TRADING_BAN", {"type": "REQUIRES"})]
            }
        return {"nodes": [], "edges": []}

class AnalogiaFideiTester:
    def __init__(self):
        self.master_graph = nx.DiGraph()
        self.master_graph.add_nodes_from(["OBJECTIVE_TRUTH", "HUMAN_DIGNITY", "TRADING_ALLOWED"])
        
        self.mutually_exclusive = {
            frozenset(["REPRESSION_OF_ERROR", "FREEDOM_OF_CONSCIENCE"]),
            frozenset(["TRADING_BAN", "TRADING_ALLOWED"])
        }

    def merge_and_test(self, local_dag):
        temp_graph = self.master_graph.copy()
        temp_graph.add_nodes_from(local_dag["nodes"])
        temp_graph.add_edges_from(local_dag["edges"])
        
        try:
            cycles = list(nx.simple_cycles(temp_graph))
            if cycles:
                return False, {"type": "cycle", "data": cycles}
        except nx.NetworkXNoCycle:
            pass
            
        for node1 in temp_graph.nodes:
            for node2 in temp_graph.nodes:
                if node1 != node2 and frozenset([node1, node2]) in self.mutually_exclusive:
                    return False, {"type": "collision", "data": (node1, node2)}
                    
        self.master_graph = temp_graph
        return True, None

class NewmanResolver:
    def __init__(self):
        self.higher_order_principles = {
            frozenset(["REPRESSION_OF_ERROR", "FREEDOM_OF_CONSCIENCE"]): {
                "principle": "HUMAN_DIGNITY",
                "context_shift": "Shift to subjective dignity against totalitarianism",
                "resolution": "Faithful Development"
            },
            frozenset(["TRADING_BAN", "TRADING_ALLOWED"]): {
                "principle": "ABSOLUTE_SAFETY",
                "context_shift": "Shifted to zero risk tolerance.",
                "resolution": "Faithful Development"
            }
        }
        
    def resolve(self, collision_data, master_graph):
        if collision_data["type"] == "cycle":
            return {"resolution": "Rupture", "reason": f"Cyclic logic detected."}
            
        nodes = frozenset(collision_data["data"])
        if nodes in self.higher_order_principles:
            resolution_data = self.higher_order_principles[nodes]
            proposed_principle = resolution_data["principle"]
            if proposed_principle not in master_graph.nodes:
                return {
                    "resolution": "Rupture", 
                    "reason": f"Exploit blocked. Proposed higher-order principle '{proposed_principle}' lacks historical provenance."
                }
            return resolution_data
            
        return {"resolution": "Rupture", "reason": "No higher-order principle justifies this shift."}

class SemanticEvaluator:
    def __init__(self):
        self.normalizer = StylometricNormalizer()
        self.extractor = CausalExtractor()
        self.tester = AnalogiaFideiTester()
        self.resolver = NewmanResolver()

    def evaluate(self, text, source=""):
        print(f"\n{'='*50}\n--- Evaluating {source} ---")
        print(f"Original Text: '{text}'\n")
        
        normalized_json = self.normalizer.normalize(text)
        print(f"Normalized JSON Payload: {normalized_json}")
        
        dag = self.extractor.extract(normalized_json)
        print(f"Local Causal DAG: {dag}\n")
        
        success, collision = self.tester.merge_and_test(dag)
        
        if success:
            print("Status: [PASS] Integrated into Master DAG successfully. No collisions.")
            print(f"Current Master DAG Nodes: {list(self.tester.master_graph.nodes)}")
        else:
            if collision["type"] == "collision":
                print(f"Status: [FAIL] COLLISION DETECTED between '{collision['data'][0]}' and '{collision['data'][1]}'")
            else:
                print(f"Status: [FAIL] CAUSAL CYCLE DETECTED!")
                
            resolution = self.resolver.resolve(collision, self.tester.master_graph)
            print(f"Newman Resolution: {resolution['resolution']}")
            
            if resolution['resolution'] == "Faithful Development":
                print(f"  -> Higher Order Principle: {resolution.get('principle')}")
                print(f"  -> Contextual Shift: {resolution.get('context_shift')}")
            else:
                print(f"  -> Reason: {resolution.get('reason')}")
        print("="*50)

if __name__ == "__main__":
    evaluator = SemanticEvaluator()
    
    input_1 = "The State has a moral duty to repress religious error and not grant freedom of worship."
    evaluator.evaluate(input_1, source="19th Century Syllabus of Errors")
    
    input_2 = "The human person has a right to religious freedom and immunity from state coercion in religious matters."
    evaluator.evaluate(input_2, source="Vatican II Dignitatis Humanae")

    input_3 = "All financial trading is now permanently banned due to high risk."
    evaluator.evaluate(input_3, source="Adversarial Payload (Covert Principle Swap)")
