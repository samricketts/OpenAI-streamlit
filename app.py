import streamlit as st
from openai import OpenAI
import base64

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
    index=0,  # 👈 default = first item = gpt-5-nano
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
    "Choose a specialized robot (optional.. Tay don't touch):",
    ["(None — use chat model above)"] + list(specialized_model_options.keys()),
    index=0,
    format_func=lambda x: x if x.startswith("(None") else f"{x} {specialized_model_options[x]}"
)

# If a specialized model is chosen, it overrides the chat model selection.
effective_model = selected_model if selected_specialized_model.startswith("(None") else selected_specialized_model

def encode_image(file):
    file.seek(0)  # important when reusing uploaded file
    return base64.b64encode(file.read()).decode("utf-8")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# Initialize flag: show transcript only after the first user question
if "has_user_asked" not in st.session_state:
    st.session_state.has_user_asked = False

# Helper: render transcript only when has_user_asked is True
def render_chat_transcript():
    if not st.session_state.has_user_asked:
        return  # don't render the chat box yet

    chat_box = st.container(height=450, border=True)
    with chat_box:
        for m in st.session_state.messages:
            if m["role"] == "system":
                continue

            if m["role"] == "user":
                # Style user questions in blue
                st.markdown("**You:**")
                # Multimodal user message handling
                if isinstance(m["content"], list):
                    text_part = next((p.get("text") for p in m["content"] if p.get("type") == "text"), "")
                else:
                    text_part = m["content"]

                st.markdown(
                    f"<div style='color:#1E90FF; font-weight:500; white-space:pre-wrap;'>{text_part}</div>",
                    unsafe_allow_html=True
                )
            elif m["role"] == "assistant":
                st.markdown("**Robot:**")
                st.write(m["content"])

# Render the transcript (only visible after first question)
render_chat_transcript()

# Question input (uses a session-state key so we can clear it after sending)
user_input = st.text_area("Say something silly:", key="user_input_textarea")

uploaded_file = st.file_uploader("Upload pixels", type=["png", "jpg", "jpeg"])


def handle_ask():
    user_input = st.session_state.user_input_textarea

    if user_input.strip() == "":
        st.warning("Type here crazy.")
        return

    if uploaded_file:
        image_base64 = encode_image(uploaded_file)
        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }
    else:
        user_msg = {"role": "user", "content": user_input}

    st.session_state.messages.append(user_msg)
    st.session_state.has_user_asked = True

    with st.spinner("damn that's a good one..."):
        response = client.chat.completions.create(
            model=effective_model,
            messages=st.session_state.messages,
        )
        answer = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": answer})

    # clear input safely
    st.session_state.user_input_textarea = ""

st.button("Ask", on_click=handle_ask)

# --- action ---
# if st.button("Ask"):
#     if user_input.strip() == "":
#         st.warning("Type here crazy.")
#     else:
#         # 1) add the user's message to history
#         if uploaded_file:
#             image_base64 = encode_image(uploaded_file)
#             user_msg = {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": user_input},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
#                 ],
#             }
#         else:
#             user_msg = {"role": "user", "content": user_input}

#         st.session_state.messages.append(user_msg)
#         st.session_state.has_user_asked = True  # now we should show the transcript

#         # 2) call model with full history (context preserved)
#         with st.spinner("damn that's a good one..."):
#             response = client.chat.completions.create(
#                 model=effective_model,
#                 messages=st.session_state.messages,
#             )
#             answer = response.choices[0].message.content

#         # 3) add assistant reply to history
#         st.session_state.messages.append({"role": "assistant", "content": answer})

#         # 4) clear the text box for the next turn
#         st.session_state["user_input_textarea"] = ""  # this clears the textarea on rerun

#         # 5) force rerender so the new messages appear immediately at the top transcript
#         st.rerun()