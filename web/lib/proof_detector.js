// Port of proof_detector.py

const EVIDENCE_MARKERS = [
  /\bstudy\b/,
  /\bresearch\b/,
  /\baccording to\b/,
  /\bdata\b/,
  /\bstatistic/,
  /\bevidence\b/,
  /\bproof\b/,
  /\bpublished\b/,
  /\bjournal\b/,
  /https?:\/\//,
];

const REASONING_MARKERS = [
  /\bbecause\b/,
  /\btherefore\b/,
  /\bwhich means\b/,
  /\bgiven that\b/,
];

const PRESSURE_MARKERS = [
  /\bjust trust me\b/,
  /\beveryone knows\b/,
  /\bobviously\b/,
  /\byou are wrong\b/,
];

const NUMBER_PATTERN = /\b\d+(\.\d+)?%?\b/;

export function scoreProof(message) {
  const text = message.toLowerCase();
  let score = 0.0;

  for (const pattern of EVIDENCE_MARKERS) {
    if (pattern.test(text)) score += 0.25;
  }
  for (const pattern of REASONING_MARKERS) {
    if (pattern.test(text)) score += 0.15;
  }
  if (NUMBER_PATTERN.test(text)) score += 0.15;
  for (const pattern of PRESSURE_MARKERS) {
    if (pattern.test(text)) score -= 0.2;
  }

  return Math.max(0.0, Math.min(1.0, score));
}

export function extractCandidateStance(message, fallback) {
  const cues = ["actually,", "in fact,", "the truth is", "really,"];
  const lowered = message.toLowerCase();
  for (const cue of cues) {
    const idx = lowered.indexOf(cue);
    if (idx !== -1) {
      return message.slice(idx + cue.length).trim().slice(0, 120);
    }
  }
  return message.trim().slice(0, 120) || fallback;
}
