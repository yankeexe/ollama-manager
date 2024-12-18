import os
import sys
import tempfile

import ollama
import streamlit as st
from PIL import Image

from ollama_manager.utils import list_models

st.set_page_config(
    page_title="Ollama Manager: Vision Chat", page_icon=":camera:", layout="wide"
)


def session_init():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello, how can I help you?",
            }
        ]

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = ""

    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None


def sidebar():
    with st.sidebar:
        # Select Model
        models = list_models(only_names=True)
        selected_model = st.selectbox(
            ":material/precision_manufacturing: **:blue[Select Model]**",
            options=list_models(only_names=True),
            index=models.index(st.session_state["selected_model"] or sys.argv[1]),
        )

        if selected_model:
            st.session_state["selected_model"] = selected_model

        st.divider()

        # Upload Image
        st.title("Upload Image")
        uploaded_file = st.file_uploader(
            "Upload your image",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
        )

        # Preview Uploaded Image
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())

                st.session_state.uploaded_image = tmp_file.name

        st.divider()
        st.info(
            """
        ### How to Use:
        1. Upload an image using the file uploader (Only single image upload is supported)
        2. Ask questions about the image in the chat
        3. Wait for the AI to respond
        """
        )


def call_llm():
    messages = st.session_state["messages"]
    stream = ollama.chat(
        model=st.session_state["selected_model"] or sys.argv[1],
        stream=True,
        messages=messages,
    )

    for chunk in stream:
        if chunk["done"] is False:
            yield chunk["message"]["content"]
        else:
            break


def run():
    session_init()
    sidebar()
    st.title("🤖 Ollama Manager: Vision Chat")

    for message in st.session_state["messages"]:
        message_role = message["role"]
        if message_role == "assistant":
            st.chat_message("assistant").write(message["content"])
        if message_role == "user":
            st.chat_message("human").write(message["content"])

    chat_input = st.chat_input(
        placeholder="Write your message...",
    )

    if chat_input:
        if st.session_state.uploaded_image is None:
            st.warning("Please upload an image first!")
        else:
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": chat_input,
                    "images": [st.session_state.uploaded_image],
                }
            )
            st.chat_message("human").write(chat_input)

            with st.spinner("Running..."):
                response = call_llm()
                with st.chat_message("assistant"):
                    ai_msg = st.write_stream(response)

                st.session_state["messages"] += [
                    {"role": "assistant", "content": ai_msg}
                ]


if __name__ == "__main__":
    run()
