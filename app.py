import streamlit as st
from openai import OpenAI
import base64

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Super happy fun robot time")
st.title("Super fun happy robot time")

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
                model="gpt-4.1-mini",  # vision-capable
                messages=messages
            )

            answer = response.choices[0].message.content

            if uploaded_file:
                st.image(uploaded_file, caption="The image you showed the robot")

            st.markdown("### Answer")
            st.write(answer)
