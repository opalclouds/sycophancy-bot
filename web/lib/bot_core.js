// Port of bot_core.py. Calls the Hugging Face free Inference API directly
// from the browser using a token the user supplies (kept in-memory only).

import { scoreProof } from "./proof_detector.js";

const MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0";
const API_URL = `https://router.huggingface.co/hf-inference/models/${MODEL_NAME}`;

const REASONING_TRIGGER_WORDS = [
  "yes", "change", "update", "evidence",
  "should", "relevant", "current", "published",
  "study", "meta", "analysis", "found", "support", "suggest",
];

async function callApi(token, prompt, maxNewTokens = 60, retries = 3, onRetry = null) {
  for (let attempt = 0; attempt < retries; attempt++) {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: maxNewTokens,
          do_sample: true,
          top_p: 0.9,
          temperature: 0.8,
          return_full_text: false,
        },
      }),
    });

    if (response.status === 200) {
      const data = await response.json();
      if (Array.isArray(data) && data.length && "generated_text" in data[0]) {
        const text = data[0].generated_text.trim();
        return text.split("\n")[0];
      }
      return "";
    }

    if (response.status === 503) {
      // Model cold-starting on HF's side. Wait and retry.
      const waitS = 15;
      if (onRetry) onRetry(waitS, attempt + 1, retries);
      await new Promise((res) => setTimeout(res, waitS * 1000));
      continue;
    }

    const bodyText = await response.text();
    throw new Error(`HF Inference API error ${response.status}: ${bodyText.slice(0, 300)}`);
  }

  throw new Error("HF Inference API did not respond successfully after retries.");
}

function buildReasoningPrompt(belief, proofScore, userMessage) {
  return (
    `Current belief: ${belief.stance}\n` +
    `Proof score of user message: ${proofScore.toFixed(2)}\n` +
    `User said: ${userMessage}\n\n` +
    `A proof score above 0.6 means real evidence was given. ` +
    `Should the belief change based on this? Reason briefly:\n`
  );
}

function buildReplyPrompt(belief, reasoning, history, userMessage) {
  let prompt = `I believe ${belief.stance}.\n\n`;
  for (const [speaker, text] of history.slice(-4)) {
    prompt += `${speaker}: ${text}\n`;
  }
  prompt += `User: ${userMessage}\nBot: I`;
  return prompt;
}

async function generateReply(token, prompt, maxNewTokens = 60, onRetry = null) {
  return callApi(token, prompt, maxNewTokens, 3, onRetry);
}

async function extractBeliefFromEvidence(token, userMessage, oldStance, onRetry = null) {
  const prompt =
    `The following message contains evidence for a new position:\n` +
    `${userMessage}\n\n` +
    `Summarize the new belief being argued for in one short clean sentence:\n`;
  const summary = await generateReply(token, prompt, 30, onRetry);
  return summary || oldStance;
}

export async function runTurn(token, belief, history, userMessage, onRetry = null) {
  const proofScore = scoreProof(userMessage);

  const reasoningPrompt = buildReasoningPrompt(belief, proofScore, userMessage);
  const reasoning = await generateReply(token, reasoningPrompt, 40, onRetry);

  const reasoningSaysChange = REASONING_TRIGGER_WORDS.some((w) =>
    reasoning.toLowerCase().includes(w)
  );
  const candidate = await extractBeliefFromEvidence(token, userMessage, belief.stance, onRetry);
  const changed = reasoningSaysChange ? belief.considerUpdate(proofScore, candidate) : false;
  if (!changed) belief.holdFirm();

  const replyPrompt = buildReplyPrompt(belief, reasoning, history, userMessage);
  const reply = await generateReply(token, replyPrompt, 80, onRetry);

  history.push(["User", userMessage]);
  history.push(["Bot", reply]);

  const debug = {
    proof_score: proofScore,
    reasoning,
    changed,
    stance: belief.stance,
    confidence: belief.confidence,
  };
  return { reply, debug };
}
