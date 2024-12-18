import sys

import ollama
import streamlit as st

from ollama_manager.utils import list_models

st.set_page_config(page_title="Chat: Ollama Manager")


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


def sidebar():
    with st.sidebar:
        models = list_models(only_names=True)
        selected_model = st.selectbox(
            ":material/precision_manufacturing: **:blue[Select Model]**",
            options=list_models(only_names=True),
            index=models.index(st.session_state["selected_model"] or sys.argv[1]),
        )

        if selected_model:
            st.session_state["selected_model"] = selected_model

        st.divider()
        st.slider(label="top_p", value=1.0, min_value=0.0, max_value=1.0, key="top_p")
        st.slider(
            label="top_k", value=60.0, min_value=0.0, max_value=100.0, key="top_k"
        )
        st.slider(
            label="temperature",
            value=0.7,
            min_value=0.0,
            max_value=1.0,
            key="temperature",
        )
        st.slider(
            label="Context Length",
            min_value=1000,
            max_value=9999,
            key="context_length",
            value=4000,
        )
        st.divider()
        st.caption("[:zap: Ollama Manager](https://github.com/yankeexe/ollama-manager)")
        st.caption(
            "[:bug: Report Issues](https://github.com/yankeexe/ollama-manager/issues)"
        )


def call_llm():
    messages = st.session_state["messages"]
    stream = ollama.chat(
        model=st.session_state["selected_model"] or sys.argv[1],
        stream=True,
        messages=messages,
        options={
            "temperature": st.session_state["temperature"],
            "top_k": st.session_state["top_k"],
            "top_p": st.session_state["top_p"],
            "num_ctx": st.session_state["context_length"],
        },
    )

    for chunk in stream:
        if chunk["done"] is False:
            yield chunk["message"]["content"]
        else:
            break


def run():
    session_init()
    sidebar()
    st.header("🦙 Ollama Manager: Chat Application")

    for message in st.session_state["messages"]:
        message_role = message.get("role")
        if message_role == "assistant":
            st.chat_message("assistant").write(message["content"])
        if message_role == "user":
            st.chat_message("human").write(message["content"])

    chat_input = st.chat_input(
        placeholder="Write your message...",
    )

    if chat_input:
        st.session_state["messages"] += [{"role": "user", "content": chat_input}]
        st.chat_message("human").write(chat_input)
        response = call_llm()
        with st.chat_message("assistant"):
            ai_msg = st.write_stream(response)

        st.session_state["messages"] += [{"role": "assistant", "content": ai_msg}]


if __name__ == "__main__":
    run()
