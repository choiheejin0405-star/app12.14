import streamlit as st
import google.generativeai as genai
import os

# [중요] dotenv 관련 코드를 아예 삭제했습니다.
# 이제 라이브러리 설치 문제로 에러가 날 일이 없습니다.

st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")

st.title("🤖 Gemini 챗봇 (최종 수정)")

# 사이드바에서 API 키 입력받기
with st.sidebar:
    st.header("설정")
    # Streamlit Secrets에서 키를 가져오거나, 없으면 빈 값
    # (dotenv 대신 Streamlit 자체 기능을 쓰거나 직접 입력을 받습니다)
    if "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
    else:
        default_key = ""
        
    api_key = st.text_input("Google API Key 입력", value=default_key, type="password")

# API 키가 없으면 경고
if not api_key:
    st.warning("왼쪽 사이드바에 API 키를 입력해주세요.")
    st.stop()

# Gemini 설정 (가장 안정적인 모델 사용)
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# 채팅 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 채팅 입력
if prompt := st.chat_input("메시지 입력..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            message_placeholder.error(f"오류 발생: {e}")
