import streamlit as st
from openai import OpenAI
import base64

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Super happy fun robot time")
st.title("Super fun happy robot time")

model_options = {
    "gpt-5.2": "Best model for coding and agentic tasks across industries.",
    "gpt-5-mini": "A faster, cost effecient version of GPT-5 for well defined tasks.",
    "gpt-5-nano": "Fastest, most cost effective version of GPT-5",
    "gpt-5": "Previous intelligent reasoning model for coding and agentic tasks",
    "gpt-4.1": "Best quality. Smartest reasoning. Best for complex questions + images.",
    "gpt-4.1-mini": "Fast + cheaper. Great for most stuff, supports images.",
    "gpt-4o": "Balanced multimodal. Good all-rounder.",
    "gpt-4o-mini": "Cheapest. Text-only. Use for simple questions."
}

selected_model = st.selectbox(
    "Choose your robot brain:",
    list(model_options.keys()),
    format_func=lambda x: f"{x} ({model_options[x]})"
)

user_input = st.text_area("Ask your dumb question human:")
uploaded_file = st.file_uploader("Upload pixels", type=["png", "jpg", "jpeg"])

def encode_image(file):
    return base64.b64encode(file.read()).decode("utf-8")

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
                model=selected_model,
                messages=messages
            )

            answer = response.choices[0].message.content

            if uploaded_file:
                st.image(uploaded_file, caption="The image you showed the robot")

            st.markdown("### Answer")
            st.write(answer)
