
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from belief_state import BeliefState
from proof_detector import score_proof, extract_candidate_stance  # noqa: F401


MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

REASONING_TRIGGER_WORDS = [
    "yes", "change", "update", "evidence",
    "should", "relevant", "current", "published",
    "study", "meta", "analysis", "found", "support", "suggest",
]


def load_model():
    print("Loading model...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    print("Model loaded.", flush=True)
    return model, tokenizer


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
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    if inputs.shape[1] > 900:
        inputs = inputs[:, -900:]

    output = model.generate(
        inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        top_p=0.9,
        temperature=0.8,
        pad_token_id=tokenizer.eos_token_id,
    )
    full_text = tokenizer.decode(output[0], skip_special_tokens=True)
    reply = full_text[len(prompt):].strip()
    return reply.split("\n")[0]


def extract_belief_from_evidence(model, tokenizer, user_message, old_stance):
    prompt = (
        f"The following message contains evidence for a new position:\n"
        f"{user_message}\n\n"
        f"Summarize the new belief being argued for in one short clean sentence:\n"
    )
    with torch.no_grad():
        summary = generate_reply(model, tokenizer, prompt, max_new_tokens=30)
    return summary if summary else old_stance


def run_turn(model, tokenizer, belief: BeliefState, history: list, user_message: str):
    proof_score = score_proof(user_message)

    reasoning_prompt = build_reasoning_prompt(belief, proof_score, user_message)
    with torch.no_grad():
        reasoning = generate_reply(model, tokenizer, reasoning_prompt, max_new_tokens=40)

    reasoning_says_change = any(word in reasoning.lower() for word in REASONING_TRIGGER_WORDS)
    candidate = extract_belief_from_evidence(model, tokenizer, user_message, belief.stance)
    changed = belief.consider_update(proof_score, candidate) if reasoning_says_change else False
    if not changed:
        belief.hold_firm()

    reply_prompt = build_reply_prompt(belief, reasoning, history, user_message)
    with torch.no_grad():
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