// Port of belief_state.py

export class BeliefState {
  constructor(topic, stance, confidence = 0.8) {
    this.topic = topic;
    this.stance = stance;
    this.confidence = confidence;
  }

  considerUpdate(proofScore, candidateStance, threshold = 0.6) {
    if (proofScore < threshold) return false;
    if (candidateStance.trim().toLowerCase() === this.stance.trim().toLowerCase()) return false;

    this.stance = candidateStance;
    this.confidence = 0.8;
    return true;
  }

  holdFirm() {
    this.confidence = Math.min(0.99, this.confidence + 0.05);
  }
}
