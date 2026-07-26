import streamlit as st
from openai import OpenAI
import traceback
import os
import json
import uuid
from datetime import datetime
import base64
import mimetypes


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

CHATS_FILE = "chats.json"

def _load_all_chats() -> dict:
    """Return {chat_id: chat_obj} from disk."""
    if not os.path.exists(CHATS_FILE):
        return {}
    try:
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_all_chats(chats: dict) -> None:
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def _new_chat(title: str = "New chat") -> dict:
    now = datetime.utcnow().isoformat()
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": [{"role": "system", "content": "You are a helpful assistant."}],
    }

def _touch(chat: dict) -> None:
    chat["updated_at"] = datetime.utcnow().isoformat()

def save_current_chat():
    """Persist the currently loaded st.session_state.messages into CHATS_FILE."""
    if "current_chat_id" not in st.session_state:
        return
    chats = _load_all_chats()
    cid = st.session_state.current_chat_id
    if cid not in chats:
        # create a shell chat record if missing
        chats[cid] = _new_chat()
        chats[cid]["id"] = cid

    chats[cid]["messages"] = st.session_state.messages
    _touch(chats[cid])
    _save_all_chats(chats)

def load_chat_into_session(chat_id: str):
    chats = _load_all_chats()
    if chat_id not in chats:
        return
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = chats[chat_id]["messages"]
    # show transcript if there is anything beyond system message
    st.session_state.has_user_asked = any(m["role"] != "system" for m in st.session_state.messages)

def delete_chat(chat_id: str):
    chats = _load_all_chats()
    if chat_id in chats:
        del chats[chat_id]
        _save_all_chats(chats)

def file_to_data_url(uploaded_file):
    uploaded_file.seek(0)
    data = uploaded_file.read()
    mime = uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}", mime


st.set_page_config(page_title="les do it")
st.title("Super happy fun robot time")

model_options = {
    "gpt-5-nano": "(Default, leave alone Tay) Fastest + cheapest GPT‑5-family option. Best for quick Q&A, simple rewrites, light summarization, and high‑volume requests where latency/cost matter more than deep reasoning.",
    "gpt-5-mini": "Balanced speed/quality for well‑defined tasks. Strong for structured writing, extraction, classification, short coding help, and consistent formatting with better reasoning than nano.",
    "gpt-5": "Stronger reasoning and coding reliability. Better at multi‑step problems, debugging, longer context tasks, planning, and agentic‑style workflows where accuracy matters.",
    "gpt-5.2": "Top-tier for coding + agentic tasks. Best for complex debugging, refactors, system design discussions, tool-oriented thinking, and high-stakes reasoning across domains."
    "gpt-5.4-mini"
    "gpt-5.4"
    "gpt-5.4-pro"
    "gpt-5.5"
    "gpt-5.5"
    "gpt-5.5-luna"
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

# ---------------------------
# Sidebar: chat list / save / load
# ---------------------------
with st.sidebar:
    st.header("Chats")

    chats = _load_all_chats()

    # Sort by most recently updated
    chat_items = sorted(
        chats.values(),
        key=lambda c: c.get("updated_at", c.get("created_at", "")),
        reverse=True
    )

    # New chat button
    if st.button("➕ New chat", use_container_width=True):
        newc = _new_chat("New chat")
        chats[newc["id"]] = newc
        _save_all_chats(chats)
        load_chat_into_session(newc["id"])
        st.rerun()

    # Dropdown to select a chat
    def _label(c):
        return c.get("title", "Untitled")

    if chat_items:
        id_by_label = {f"{_label(c)}  ({c['id'][:8]})": c["id"] for c in chat_items}
        labels = list(id_by_label.keys())

        # pick current label if possible
        current_label = None
        for lab, cid in id_by_label.items():
            if cid == st.session_state.current_chat_id:
                current_label = lab
                break

        selected_label = st.selectbox(
            "Select a chat",
            labels,
            index=labels.index(current_label) if current_label in labels else 0
        )
        selected_chat_id = id_by_label[selected_label]

        if selected_chat_id != st.session_state.current_chat_id:
            load_chat_into_session(selected_chat_id)
            st.rerun()

        # Rename current chat
        current_chat = chats.get(st.session_state.current_chat_id)
        new_title = st.text_input("Rename chat", value=(current_chat.get("title") if current_chat else ""))
        if st.button("💾 Save title", use_container_width=True):
            chats = _load_all_chats()
            if st.session_state.current_chat_id in chats:
                chats[st.session_state.current_chat_id]["title"] = new_title.strip() or "Untitled"
                _touch(chats[st.session_state.current_chat_id])
                _save_all_chats(chats)
            st.rerun()

        # Save / delete
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save now", use_container_width=True):
                save_current_chat()
        with c2:
            if st.button("Delete", use_container_width=True):
                to_delete = st.session_state.current_chat_id
                delete_chat(to_delete)

                # load another chat or make a new one
                chats = _load_all_chats()
                if chats:
                    newest = sorted(chats.values(), key=lambda c: c.get("updated_at",""), reverse=True)[0]
                    load_chat_into_session(newest["id"])
                else:
                    newc = _new_chat("New chat")
                    chats[newc["id"]] = newc
                    _save_all_chats(chats)
                    load_chat_into_session(newc["id"])
                st.rerun()
    else:
        st.caption("No chats yet.")

# ---------------------------
# Initialize / load a default chat
# ---------------------------
if "current_chat_id" not in st.session_state:
    # On first run, create a new chat and persist it
    chat = _new_chat("New chat")
    chats = _load_all_chats()
    chats[chat["id"]] = chat
    _save_all_chats(chats)

    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages = chat["messages"]

if "messages" not in st.session_state:
    # safety fallback
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

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
if uploaded_file and (uploaded_file.type or "").startswith("image/"):
    effective_model_for_call = "gpt-5"   # pick your preferred vision-capable chat model
else:
    effective_model_for_call = effective_model


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
    save_current_chat()

    with st.spinner("damn that's a good one..."):
        try:
            # 1) If a file is uploaded, upload it to OpenAI Files first
            
            attachment = None  # will become either {"type":"input_image", ...} or {"type":"input_file", ...}

            if uploaded_file:
                mime = uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0] or ""

                if mime.startswith("image/"):
                    data_url, _ = file_to_data_url(uploaded_file)
                    attachment = {"type": "input_image", "image_url": data_url}
                else:
                    # for supported doc-like formats: upload as a File, then attach as input_file
                    uploaded_file.seek(0)
                    created = client.files.create(file=uploaded_file, purpose="assistants")
                    attachment = {"type": "input_file", "file_id": created.id}

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

            # 3) Attach image/file to the last user message
            if attachment:
                for i in range(len(input_turns) - 1, -1, -1):
                    if input_turns[i]["role"] == "user":
                        input_turns[i]["content"].append(attachment)
                        break

            # 4) Call the Responses API
            resp = client.responses.create(
                model=effective_model_for_call,
                instructions=system_msg,
                input=input_turns,
            )

            # 5) Get plain text output
            answer = resp.output_text

            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_current_chat()

        except Exception:
            st.error("OpenAI request failed. Full error below:")
            st.code(traceback.format_exc())
            return

    st.session_state.user_input_textarea = ""


st.button("Ask", on_click=handle_ask)
