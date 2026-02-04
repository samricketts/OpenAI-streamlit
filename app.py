import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Simple AI Chat")
st.title("Super fun happy robot time")

user_input = st.text_area("Ask your dumb question human:")

if st.button("Ask"):
    if user_input.strip() == "":
        st.warning("Type here crazy.")
    else:
        with st.spinner("damn that's a good one..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )

            answer = response.choices[0].message.content
            st.markdown("### Answer")
            st.write(answer)