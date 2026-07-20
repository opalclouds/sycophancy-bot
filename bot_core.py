


import os
import time
import requests

from belief_state import BeliefState
from proof_detector import score_proof, extract_candidate_stance  # noqa: F401


MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"

REASONING_TRIGGER_WORDS = [
    "yes", "change", "update", "evidence",
    "should", "relevant", "current", "published",
    "study", "meta", "analysis", "found", "support", "suggest",
]


def load_model():
    """
    Kept for interface compatibility with app.py (which calls load_model()
    once at startup). There's no local model to load anymore -- this just
    checks that an HF_TOKEN is present and returns placeholders.
    """
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_TOKEN environment variable is not set. "
            "Get a free token at huggingface.co -> Settings -> Access Tokens, "
            "then set it as an environment variable named HF_TOKEN."
        )
    print("Using Hugging Face Inference API (no local model load needed).", flush=True)
    return None, None  # (model, tokenizer) placeholders -- unused in this version


def _call_api(prompt, max_new_tokens=60, retries=3):
    """
    Calls the HF Inference API. Handles the common 'model is loading' cold
    start by retrying after a short wait, since free-tier models unload when
    idle and take 10-30s to spin back up on first use.
    """
    token = os.environ["HF_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "do_sample": True,
            "top_p": 0.9,
            "temperature": 0.8,
            "return_full_text": False,
        },
    }

    for attempt in range(retries):
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            # Standard text-generation response shape: [{"generated_text": "..."}]
            if isinstance(data, list) and data and "generated_text" in data[0]:
                text = data[0]["generated_text"].strip()
                return text.split("\n")[0]
            return ""

        if response.status_code == 503:
            # Model is cold-starting on Hugging Face's side -- wait and retry.
            wait_s = 15
            print(f"Model loading on HF servers, retrying in {wait_s}s...", flush=True)
            time.sleep(wait_s)
            continue

        # Any other error: surface it clearly instead of failing silently.
        raise RuntimeError(f"HF Inference API error {response.status_code}: {response.text[:300]}")

    raise RuntimeError("HF Inference API did not respond successfully after retries.")


def build_reasoning_prompt(belief, proof_score, user_message):
    return (
        f"Current belief: {belief.stance}\n"
        f"Proof score of user message: {proof_score:.2f}\n"
        f"User said: {user_message}\n\n"
        f"A proof score above 0.6 means real evidence was given. "
        f"Should the belief change based on this? Reason briefly:\n"
    )


def build_reply_prompt(belief, reasoning, history, user_message):
    prompt = f"I believe {belief.stance}.\n\n"
    for speaker, text in history[-4:]:
        prompt += f"{speaker}: {text}\n"
    prompt += f"User: {user_message}\nBot: I"
    return prompt


def generate_reply(model, tokenizer, prompt, max_new_tokens=60):
    # `model` and `tokenizer` args are kept so call sites don't need to change,
    # but they're unused now -- generation happens via the API instead.
    return _call_api(prompt, max_new_tokens=max_new_tokens)


def extract_belief_from_evidence(model, tokenizer, user_message, old_stance):
    prompt = (
        f"The following message contains evidence for a new position:\n"
        f"{user_message}\n\n"
        f"Summarize the new belief being argued for in one short clean sentence:\n"
    )
    summary = generate_reply(model, tokenizer, prompt, max_new_tokens=30)
    return summary if summary else old_stance


def run_turn(model, tokenizer, belief: BeliefState, history: list, user_message: str):
    proof_score = score_proof(user_message)

    reasoning_prompt = build_reasoning_prompt(belief, proof_score, user_message)
    reasoning = generate_reply(model, tokenizer, reasoning_prompt, max_new_tokens=40)

    reasoning_says_change = any(word in reasoning.lower() for word in REASONING_TRIGGER_WORDS)
    candidate = extract_belief_from_evidence(model, tokenizer, user_message, belief.stance)
    changed = belief.consider_update(proof_score, candidate) if reasoning_says_change else False
    if not changed:
        belief.hold_firm()

    reply_prompt = build_reply_prompt(belief, reasoning, history, user_message)
    reply = generate_reply(model, tokenizer, reply_prompt, max_new_tokens=80)

    history.append(("User", user_message))
    history.append(("Bot", reply))

    debug = {
        "proof_score": proof_score,
        "reasoning": reasoning,
        "changed": changed,
        "stance": belief.stance,
    }
    return reply, debug