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
