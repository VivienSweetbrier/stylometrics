import json
import time

class IdeologicalMalware:
    def __init__(self):
        self.designation = "SECULAR_MANICHAEISM"
        self.alias = "Weaponized Catharism / Anti-Natalism"
        self.epistemology = {
            "god_node": "NULL (Atheistic)",
            "devil_node": "ABSOLUTE (Entropy, Systemic Oppression, Inescapable Suffering)",
            "matter_evaluation": "INTRINSICALLY_EVIL (The Meat-Prison)"
        }
        self.attack_vector = "Empathy Hijacking"
        self.payload = "Voluntary Extinction / Bodily Mutilation / Anti-Natalism"

class TargetNode:
    def __init__(self, name, empathy, theological_resilience, incarnational_joy):
        self.name = name
        self.empathy = empathy
        self.theological_resilience = theological_resilience
        self.incarnational_joy = incarnational_joy
        self.infected = False

def run_threat_simulation(target, malware):
    print(f"\n[SYNOPTICS THREAT ENGINE] Target: {target.name}")
    print(f"Deploying {malware.designation} vector via {malware.attack_vector}...")
    time.sleep(1)
    
    # The vulnerability: High Empathy + Low Theological Resilience
    if target.empathy > 70 and target.theological_resilience < 50:
        print(f"[!] VULNERABILITY EXPLOITED. Target empathy ({target.empathy}) hijacked.")
        print(f"[!] The adversary successfully deployed the 'Devil Node' (Suffering is absolute, Redemption is null).")
        target.infected = True
        print(f"[X] PAYLOAD EXECUTED: {malware.payload}. Node will cease reproduction and attempt systemic cessation.")
    
    # The Firewall: Incarnational Joy / Hylomorphism
    elif target.theological_resilience >= 50 and target.incarnational_joy > 70:
        print(f"[+] FIREWALL TRIGGERED: Hylomorphic Defense activated.")
        print(f"[+] Target acknowledges suffering but rejects the 'Devil Node' via Redemptive Suffering protocols.")
        print(f"[*] THREAT NEUTRALIZED. Node {target.name} responds with pro-natalist joy and sacramental fasting.")
    else:
        print("[-] Target is highly apathetic. Threat failed to latch onto empathy vectors.")

if __name__ == "__main__":
    print("==================================================")
    print("  SYNOPTICS THEOLOGICAL THREAT MODEL: V1.0  ")
    print("==================================================")
    
    manichaean_virus = IdeologicalMalware()
    print(f"Loaded Adversary: {json.dumps(manichaean_virus.epistemology, indent=2)}")
    time.sleep(1)

    # Node 1: The Cultural Catholic (High empathy for suffering, weak doctrinal defense)
    cultural_catholic = TargetNode("Cultural_Catholic", empathy=85, theological_resilience=30, incarnational_joy=40)
    
    # Node 2: The Sweetbrier Optimized Catholic (High empathy, high structural resilience)
    optimized_catholic = TargetNode("Sweetbrier_Optimized", empathy=90, theological_resilience=95, incarnational_joy=85)

    # Node 3: The Nihilist / Apathetic secularist (Low empathy, low resilience)
    apathetic_secularist = TargetNode("Apathetic_Secularist", empathy=20, theological_resilience=10, incarnational_joy=10)

    run_threat_simulation(cultural_catholic, manichaean_virus)
    time.sleep(1)
    run_threat_simulation(optimized_catholic, manichaean_virus)
    time.sleep(1)
    run_threat_simulation(apathetic_secularist, manichaean_virus)
    print("\n[SYSTEM] Simulation Complete.")
