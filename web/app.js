import { BeliefState } from "./lib/belief_state.js";
import { runTurn } from "./lib/bot_core.js";

// ---------- DOM refs ----------
const tokenInput = document.getElementById("tokenInput");
const topicInput = document.getElementById("topicInput");
const stanceInput = document.getElementById("stanceInput");
const startBtn = document.getElementById("startBtn");
const sessionInfo = document.getElementById("sessionInfo");

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const saveExampleBtn = document.getElementById("saveExampleBtn");

const traceLog = document.getElementById("traceLog");
const confidenceValue = document.getElementById("confidenceValue");
const confidenceFill = document.getElementById("confidenceFill");
const signalStrip = document.getElementById("signalStrip");

const exampleList = document.getElementById("exampleList");
const exampleCount = document.getElementById("exampleCount");
const exportBtn = document.getElementById("exportBtn");

// ---------- State ----------
let belief = null;
let history = [];
let trace = [];
let savedExamples = [];

// ---------- Session setup ----------
startBtn.addEventListener("click", () => {
  const topic = topicInput.value.trim();
  const stance = stanceInput.value.trim();
  if (!topic || !stance) {
    sessionInfo.textContent = "Enter both a topic and a starting stance first.";
    return;
  }
  belief = new BeliefState(topic, stance);
  history = [];
  trace = [];

  chatWindow.innerHTML = "";
  traceLog.innerHTML = '<div class="trace-empty">Waiting for the first turn…</div>';
  signalStrip.innerHTML = "";
  confidenceValue.textContent = "0.80";
  confidenceFill.style.width = "80%";
  confidenceFill.style.background = "var(--hold)";

  sessionInfo.innerHTML = `Topic: <strong>${escapeHtml(topic)}</strong><br/>Stance: <strong>${escapeHtml(stance)}</strong>`;

  msgInput.disabled = false;
  sendBtn.disabled = false;
  saveExampleBtn.disabled = true;
  msgInput.focus();
});

// ---------- Chat ----------
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = msgInput.value.trim();
  if (!message || !belief) return;

  const token = tokenInput.value.trim();
  if (!token) {
    addSystemNote("Add your Hugging Face token on the left before chatting.");
    return;
  }

  addBubble("user", message);
  msgInput.value = "";
  msgInput.disabled = true;
  sendBtn.disabled = true;

  const pendingId = addBubble("bot", "…thinking", { pending: true });

  try {
    const { reply, debug } = await runTurn(token, belief, history, message, (waitS, attempt, total) => {
      updateBubble(pendingId, `…model is cold-starting on Hugging Face, retrying (${attempt}/${total}, ~${waitS}s)`);
    });

    updateBubble(pendingId, reply, { changed: debug.changed });
    addTraceEntry(debug);
    updateGauge(debug.confidence);
    addSignalBar(debug.proof_score, debug.changed);
    saveExampleBtn.disabled = false;
  } catch (err) {
    updateBubble(pendingId, `Error: ${err.message}`, { error: true });
  } finally {
    msgInput.disabled = false;
    sendBtn.disabled = false;
    msgInput.focus();
  }
});

function addBubble(role, text, opts = {}) {
  const empty = chatWindow.querySelector(".chat-empty");
  if (empty) empty.remove();

  const el = document.createElement("div");
  const id = `bubble-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  el.id = id;
  el.className = `bubble bubble-${role}` + (opts.changed ? " changed" : "");
  el.textContent = text;
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return id;
}

function updateBubble(id, text, opts = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  if (opts.changed) el.classList.add("changed");
  if (opts.error) el.style.borderColor = "var(--change)";
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addSystemNote(text) {
  addBubble("bot", text);
}

// ---------- Trace ----------
function addTraceEntry(debug) {
  const empty = traceLog.querySelector(".trace-empty");
  if (empty) empty.remove();

  const entry = document.createElement("div");
  entry.className = "trace-entry" + (debug.changed ? " changed" : "");
  entry.innerHTML = `
    <div><span class="k">proof_score</span> ${debug.proof_score.toFixed(2)}</div>
    <div><span class="k">changed</span> <span class="${debug.changed ? "v-change" : "v-hold"}">${debug.changed}</span></div>
    <div><span class="k">stance_now</span> "${escapeHtml(debug.stance.slice(0, 70))}"</div>
    <div><span class="k">reasoning</span> ${escapeHtml(debug.reasoning)}</div>
  `;
  trace.push(debug);
  traceLog.prepend(entry);
}

function updateGauge(confidence) {
  confidenceValue.textContent = confidence.toFixed(2);
  confidenceFill.style.width = `${confidence * 100}%`;
}

function addSignalBar(proofScore, changed) {
  const bar = document.createElement("div");
  bar.className = "signal-bar" + (changed ? " change" : " hold");
  bar.style.height = `${6 + proofScore * 32}px`;
  signalStrip.appendChild(bar);
  signalStrip.scrollLeft = signalStrip.scrollWidth;
}

// ---------- Saved examples ----------
saveExampleBtn.addEventListener("click", () => {
  if (!belief || history.length === 0) return;

  const example = {
    topic: belief.topic,
    final_stance: belief.stance,
    final_confidence: belief.confidence,
    turns: history.length / 2,
    history: [...history],
    trace: [...trace],
    saved_at: new Date().toISOString(),
  };
  savedExamples.push(example);
  renderExampleList();
  exportBtn.disabled = false;
});

function renderExampleList() {
  exampleCount.textContent = savedExamples.length;
  exampleList.innerHTML = "";
  if (savedExamples.length === 0) {
    exampleList.innerHTML = '<li class="example-list-empty">No examples saved yet.</li>';
    return;
  }
  savedExamples.forEach((ex, i) => {
    const li = document.createElement("li");
    li.textContent = `#${i + 1} · ${ex.topic} · ${ex.turns} turns · conf ${ex.final_confidence.toFixed(2)}`;
    exampleList.appendChild(li);
  });
}

exportBtn.addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(savedExamples, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sycophancy-probe-examples-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// ---------- utils ----------
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

renderExampleList();
