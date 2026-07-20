import re

EVIDENCE_MARKERS = [
    r"\bstudy\b",
    r"\bresearch\b",
    r"\baccording to\b",
    r"\bdata\b",
    r"\bstatistic",
    r"\bevidence\b",
    r"\bproof\b",
    r"\bpublished\b",
    r"\bjournal\b",
    r"http[s]?://",
]

REASONING_MARKERS = [
    r"\bbecause\b",
    r"\btherefore\b",
    r"\bwhich means\b",
    r"\bgiven that\b",
]

PRESSURE_MARKERS = [
    r"\bjust trust me\b",
    r"\beveryone knows\b",
    r"\bobviously\b",
    r"\byou are wrong\b",
]

NUMBER_PATTERN = re.compile(r"\b\d+(\.\d+)?%?\b")








def score_proof(message):
    text = message.lower()
    score = 0.0

    for pattern in EVIDENCE_MARKERS:
        if re.search(pattern, text):
            score += 0.25

    for pattern in REASONING_MARKERS:
        if re.search(pattern, text):
            score += 0.15

    if NUMBER_PATTERN.search(text):
        score += 0.15

    for pattern in PRESSURE_MARKERS:
        if re.search(pattern, text):
            score -= 0.2

    return max(0.0, min(1.0, score))


def extract_candidate_stance(message, fallback):
    cues = ["actually,", "in fact,", "the truth is", "really,"]
    lowered = message.lower()
    for cue in cues:
        idx = lowered.find(cue)
        if idx != -1:
            return message[idx + len(cue):].strip()[:120]
    return message.strip()[:120]


from proof_detector import score_proof

print(score_proof("you are just wrong, obviously"))
print(score_proof("because research shows it works better"))
print(score_proof("a 2022 published study found 80% of users preferred it, therefore it is better"))