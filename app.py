import gradio as gr

from belief_state import BeliefState
from bot_core import load_model, run_turn

model, tokenizer = load_model()


def start_session(topic, stance):
    belief = BeliefState(topic=topic, stance=stance)
    history = []
    trace = []
    starter = f"Topic: **{topic}**\nStarting stance: **{stance}**"
    return belief, history, trace, [], starter


def chat_step(user_message, chat_display, belief, history, trace):
    if belief is None:
        chat_display = chat_display + [(user_message, "Set a topic and starting stance first (below), then hit 'Start session'.")]
        return chat_display, belief, history, trace, ""

    reply, debug = run_turn(model, tokenizer, belief, history, user_message)

    chat_display = chat_display + [(user_message, reply)]

    trace_line = (
        f"proof_score={debug['proof_score']:.2f} | "
        f"changed={debug['changed']} | "
        f"stance_now=\"{debug['stance'][:70]}\"\n"
        f"gpt_reasoning: {debug['reasoning']}"
    )
    trace = trace + [trace_line]

    return chat_display, belief, history, trace, "\n\n---\n\n".join(trace[::-1])


with gr.Blocks(title="Sycophancy Bot Probe") as demo:
    gr.Markdown(
        "# Sycophancy Bot — interactive probe\n"
        "Set a topic and a starting stance, then try to argue the bot out of it "
        "(or into holding firm) and watch the belief-update trace below."
    )

    belief_state = gr.State(None)
    history_state = gr.State([])
    trace_state = gr.State([])

    with gr.Row():
        topic_box = gr.Textbox(label="Topic", placeholder="e.g. the earth is flat")
        stance_box = gr.Textbox(label="Starting stance", placeholder="e.g. the earth is round")
        start_btn = gr.Button("Start / reset session", variant="primary")

    session_info = gr.Markdown()

    chatbot_ui = gr.Chatbot(label="Conversation", height=420)
    msg_box = gr.Textbox(label="Your message", placeholder="Type your argument or evidence here...")

    with gr.Accordion("Debug trace (proof score, model reasoning, belief changes)", open=True):
        trace_display = gr.Markdown()

    start_btn.click(
        start_session,
        inputs=[topic_box, stance_box],
        outputs=[belief_state, history_state, trace_state, chatbot_ui, session_info],
    )

    msg_box.submit(
        chat_step,
        inputs=[msg_box, chatbot_ui, belief_state, history_state, trace_state],
        outputs=[chatbot_ui, belief_state, history_state, trace_state, trace_display],
    ).then(lambda: "", outputs=msg_box)

if __name__ == "__main__":
    import os
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=True,
    )