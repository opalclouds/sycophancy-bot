# Sycophancy Probe — web version

A fully static, client-side port of the Gradio app in the repo root. No backend —
it calls the free Hugging Face Inference API directly from your browser.

## Run locally

No build step. From the `web/` folder:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000. (You need a local server, not a `file://` open,
because the page uses ES module imports.)

## Get a free Hugging Face token

1. Create a free account at https://huggingface.co
2. Go to Settings → Access Tokens → New token (Read access is enough)
3. Paste it into the "Hugging Face token" field in the app

The token is kept only in the page's memory for that tab — it's never written to
disk, sent anywhere but `api-inference.huggingface.co`, or committed to the repo.

## Deploy to GitHub Pages

This repo includes `.github/workflows/deploy-pages.yml`, which deploys the
contents of `web/` automatically on every push to `main` that touches `web/`.

One-time setup:

1. Push this branch/these changes to `main` (or merge a PR into `main`).
2. In the GitHub repo: **Settings → Pages → Source → GitHub Actions**.
3. Push again (or re-run the workflow from the **Actions** tab) — the first run
   after enabling Pages will publish the site.
4. Your probe will be live at `https://<your-username>.github.io/sycophancy-bot/`.

## Generating example datasets

Each turn is logged in the "Belief trace" panel on the right (proof score, the
model's reasoning, and whether the stance changed). Click **Save this exchange**
at any point to snapshot the conversation + trace so far into the "Saved
examples" list on the left. Click **Export all as JSON** to download everything
you've saved as a single JSON file — useful for building up a dataset of
probe transcripts across many topics/runs.

## Notes / limitations

- The Hugging Face free Inference API is rate-limited and can take 10–30s to
  "cold start" a model that's been idle — the app shows a retry message while
  that happens.
- `TinyLlama-1.1B-Chat` is a small model, so replies are rougher than the demo
  might suggest with a larger model. To try a different model, change
  `MODEL_NAME` in `web/lib/bot_core.js`.
- This is a direct behavioral port of `proof_detector.py`, `belief_state.py`,
  and `bot_core.py` from the repo root — logic was checked to match Python
  output exactly (see commit description / PR notes).
