import streamlit as st
from openai import OpenAI
import base64

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Super happy fun robot time")
st.title("Super fun happy robot time")


model_options = {
    "gpt-5-nano": "(Default, leave alone Tay) Fastest + cheapest GPT‑5-family option. Best for quick Q&A, simple rewrites, light summarization, and high‑volume requests where latency/cost matter more than deep reasoning.",
    "gpt-5-mini": "Balanced speed/quality for well‑defined tasks. Strong for structured writing, extraction, classification, short coding help, and consistent formatting with better reasoning than nano.",
    "gpt-5": "Stronger reasoning and coding reliability. Better at multi‑step problems, debugging, longer context tasks, planning, and agentic-style workflows where accuracy matters.",
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
    "Choose a specialized robot (optional.. Tay, do not click here):",
    ["(None — use chat model above)"] + list(specialized_model_options.keys()),
    index=0,
    format_func=lambda x: x if x.startswith("(None") else f"{x} {specialized_model_options[x]}"
)

# If a specialized model is chosen, it overrides the chat model selection.
effective_model = selected_model if selected_specialized_model.startswith("(None") else selected_specialized_model

user_input = st.text_area("Ask your dumb question human:")
uploaded_file = st.file_uploader("Upload pixels", type=["png", "jpg", "jpeg"])

def encode_image(file):
    return base64.b64encode(file.read()).decode("utf-8")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# A single scrollable box to display the conversation chronologically
chat_box = st.container(height=450, border=True)
with chat_box:
    for m in st.session_state.messages:
        if m["role"] == "system":
            continue

        if m["role"] == "user":
            st.markdown("**You:**")
            # Handle text-only vs text+image content formats
            if isinstance(m["content"], list):
                text_part = next((p.get("text") for p in m["content"] if p.get("type") == "text"), "")
                st.write(text_part)
            else:
                st.write(m["content"])

        if m["role"] == "assistant":
            st.markdown("**Robot:**")
            st.write(m["content"])

if st.button("Ask"):
    if user_input.strip() == "":
        st.warning("Type here crazy.")
    else:
        with st.spinner("damn that's a good one..."):

            messages = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]

            # If image exists, include it
            if uploaded_file:
                image_base64 = encode_image(uploaded_file)
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_input},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model=effective_model,
                messages=messages
            )

            answer = response.choices[0].message.content

            if uploaded_file:
                st.image(uploaded_file, caption="The image you showed the robot")

            st.markdown("### Answer")
            st.write(answer)
