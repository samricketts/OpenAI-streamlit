import streamlit as st
from openai import OpenAI
import traceback

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="les do it")
st.title("Super happy fun robot time")

model_options = {
    "gpt-5-nano": "(Default, leave alone Tay) Fastest + cheapest GPT‑5-family option. Best for quick Q&A, simple rewrites, light summarization, and high‑volume requests where latency/cost matter more than deep reasoning.",
    "gpt-5-mini": "Balanced speed/quality for well‑defined tasks. Strong for structured writing, extraction, classification, short coding help, and consistent formatting with better reasoning than nano.",
    "gpt-5": "Stronger reasoning and coding reliability. Better at multi‑step problems, debugging, longer context tasks, planning, and agentic‑style workflows where accuracy matters.",
    "gpt-5.2": "Top-tier for coding + agentic tasks. Best for complex debugging, refactors, system design discussions, tool-oriented thinking, and high-stakes reasoning across domains."
}

selected_model = st.selectbox(
    "Choose your robot brain:",
    list(model_options.keys()),
    index=0,
    format_func=lambda x: f"{x} {model_options[x]}"
)

# --- Specialized models (separate dropdown) ---
specialized_model_options = {
    "sora-2-pro": "High-end generative video model. Use it when you want to create or transform video content from text prompts and/or visual references (cinematic motion, scene continuity, stylized shots). Not ideal for standard chat Q&A.",
    "o3-deep-research": "Research-focused reasoning model for deep investigations. Best for: synthesizing large/complex topics, building structured research plans, comparing sources/claims, and producing long, well-organized analytical writeups.",
    "o4-mini-deep-research": "Faster/cheaper deep-research variant. Good for: solid research summaries, outlines, and literature-style syntheses when you want the ‘research brain’ but with lower latency/cost than the largest option.",
    "gpt-image-1.5": "Image generation + editing model. Use it to create images from text, edit/transform images, generate variations, and do image-centric creative tasks. Not meant for pure text-only chat accuracy compared to GPT‑5 chat models."
}

selected_specialized_model = st.selectbox(
    "Choose a specialized model (optional.. Tay don't touch):",
    ["(None — use chat model above)"] + list(specialized_model_options.keys()),
    index=0,
    format_func=lambda x: x if x.startswith("(None") else f"{x} {specialized_model_options[x]}"
)

# If a specialized model is chosen, it overrides the chat model selection.
effective_model = selected_model if selected_specialized_model.startswith("(None") else selected_specialized_model

if "messages" not in st.session_state:
    # We'll store transcript in a simple role/content format for UI rendering,
    # and separately build Responses API input when sending.
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

if "has_user_asked" not in st.session_state:
    st.session_state.has_user_asked = False


def render_chat_transcript():
    if not st.session_state.has_user_asked:
        return

    chat_box = st.container(height=450, border=True)
    with chat_box:
        for m in st.session_state.messages:
            if m["role"] == "system":
                continue

            if m["role"] == "user":
                st.markdown("**You:**")
                st.markdown(
                    f"<div style='color:#1E90FF; font-weight:500; white-space:pre-wrap;'>{m['content']}</div>",
                    unsafe_allow_html=True
                )
            elif m["role"] == "assistant":
                st.markdown("**Robot:**")
                st.write(m["content"])


render_chat_transcript()

user_input = st.text_area("Say something silly:", key="user_input_textarea")

# Accept ANY file type
uploaded_file = st.file_uploader("Upload a file (any type)", type=None)


def handle_ask():
    user_text = (st.session_state.user_input_textarea or "").strip()
    if user_text == "":
        st.warning("Type here crazy.")
        return

    # Add user turn to transcript (for UI)
    if uploaded_file:
        user_transcript_text = f"{user_text}\n\n[Attached file: {uploaded_file.name}]"
    else:
        user_transcript_text = user_text

    st.session_state.messages.append({"role": "user", "content": user_transcript_text})
    st.session_state.has_user_asked = True

    with st.spinner("damn that's a good one..."):
        try:
            # 1) If a file is uploaded, upload it to OpenAI Files first
            file_id = None
            if uploaded_file:
                uploaded_file.seek(0)
                created = client.files.create(
                    file=uploaded_file,
                    purpose="assistants"
                )
                file_id = created.id

            # 2) Build Responses API input from our stored transcript
            #    System message goes in "instructions"
            system_msg = next((m["content"] for m in st.session_state.messages if m["role"] == "system"), "")

            # Convert transcript to Responses API "input" turns
            input_turns = []
            for m in st.session_state.messages:
                if m["role"] == "system":
                    continue
                if m["role"] == "user":
                    input_turns.append({
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": m["content"]}
                        ]
                    })
                elif m["role"] == "assistant":
                    input_turns.append({
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": m["content"]}
                        ]
                    })

            # 3) If there is an uploaded file for THIS turn, attach it to the LAST user message
            if file_id:
                # Append the file to the most recent user turn content
                for i in range(len(input_turns) - 1, -1, -1):
                    if input_turns[i]["role"] == "user":
                        input_turns[i]["content"].append({"type": "input_file", "file_id": file_id})
                        break

            # 4) Call the Responses API
            resp = client.responses.create(
                model=effective_model,
                instructions=system_msg,
                input=input_turns,
            )

            # 5) Get plain text output
            answer = resp.output_text

            st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception:
            st.error("OpenAI request failed. Full error below:")
            st.code(traceback.format_exc())
            return

    st.session_state.user_input_textarea = ""


st.button("Ask", on_click=handle_ask)
