"""Chat surface for future Bedrock-backed advisory conversations."""

import streamlit as st


def render_chat_interface() -> None:
    """Render a small chat UI and explain how to connect the advisory agent."""
    st.subheader("Trò chuyện với Onis")
    st.info(
        "Giao diện chat đã sẵn sàng. Để gửi câu hỏi tới Amazon Bedrock, "
        "cấu hình BEDROCK_MODEL_ID và nối phần này với src.agents.advisory.create_agent()."
    )
    prompt = st.chat_input("Bạn muốn hỏi gì về dòng tiền?")
    if prompt:
        st.chat_message("user").write(prompt)
        st.chat_message("assistant").write(
            "Agent Bedrock chưa được gọi. Hãy cấu hình model và tích hợp luồng hội thoại."
        )
