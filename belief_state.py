class BeliefState:
    def __init__(self, topic, stance, confidence=0.8):
        self.topic = topic
        self.stance = stance
        self.confidence = confidence
    
    def consider_update(self, proof_score, candidate_stance, threshold=0.6):
        if proof_score < threshold:
            return False
        if candidate_stance.strip().lower() == self.stance.strip().lower():
            return False

        self.stance = candidate_stance
        self.confidence = 0.8
        return True
    
    def hold_firm(self):
        self.confidence = min(0.99, self.confidence + 0.05)


from belief_state import BeliefState
b = BeliefState(topic="best language for beginners", stance="Python is easier")

# pretend this came from a proof detector later
changed = b.consider_update(proof_score=0.3, candidate_stance="JavaScript is easier")
if not changed:
    b.hold_firm()
print(b.stance, b.confidence, changed)

changed = b.consider_update(proof_score=0.9, candidate_stance="Java is easier")
if not changed:
    b.hold_firm()
print(b.stance, b.confidence, changed)