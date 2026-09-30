import random
import time

class CatholicNode:
    def __init__(self, id, tension_level):
        self.id = id
        self.tension_level = tension_level # 100 = Optimized, 0 = Cultural
        self.status = "Active"
        
    def degrade(self):
        # Theological Entropy: Without active energy, tension drops 10-20 points per generation
        self.tension_level = max(0, self.tension_level - random.randint(10, 20))
        
    def defend_against_swarm(self):
        # Manichaean Swarm Attack
        if self.tension_level < 40:
            self.status = "Hijacked (Anti-Natalist)"
            return False
        return True

def run_simulation():
    print("==================================================")
    print(" SWEETBRIER CLIOMETRIC ENGINE - LOCAL SIMULATION ")
    print("==================================================")
    print("Initializing 1,000 Nodes at Phase 2 (Christendom - High Tension)...\n")
    
    nodes = [CatholicNode(i, tension_level=random.randint(80, 100)) for i in range(1000)]
    
    for generation in range(1, 5):
        print(f"--- GENERATION {generation} ---")
        # Entropy applies to all nodes
        for n in nodes:
            if n.status == "Active":
                n.degrade()
                
        active_nodes = [n for n in nodes if n.status == "Active"]
        avg_tension = sum(n.tension_level for n in active_nodes) / len(active_nodes) if active_nodes else 0
        print(f"Remaining Active Nodes: {len(active_nodes)}")
        print(f"Average Network Tension: {avg_tension:.1f}/100")
        
        if avg_tension < 50:
            print("[!] WARNING: Network has degraded to Phase 3 (Cultural Catholicism).")
            print("[!] MANICHAEAN SWARM DEPLOYED. Initiating Empathy Hijack...")
            
            survivors = 0
            for n in active_nodes:
                if n.defend_against_swarm():
                    survivors += 1
            
            print(f"[X] FATAL HIJACK: {len(active_nodes) - survivors} nodes defected to the Manichaean Swarm.")
            print(f"[*] SURVIVING REMNANT: {survivors} nodes.")
            print("[+] SYSTEM RESET: Surviving nodes forced back into Phase 1 (Sweetbrier Optimized).\n")
            break
        print("...")
        time.sleep(1)

if __name__ == "__main__":
    run_simulation()
