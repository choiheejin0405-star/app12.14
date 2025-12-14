import streamlit as st
import requests
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="Gemini Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 엔드포인트
API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    # .env 파일에서 API 키 불러오기 시도
    st.session_state.api_key = os.getenv("GOOGLE_API_KEY", "")

# 사이드바: API 키 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key_input = st.text_input(
        "Google API Key",
        value=st.session_state.api_key,
        type="password",
        help="Gemini API 키를 입력하세요"
    )
    
    if st.button("API 키 저장"):
        st.session_state.api_key = api_key_input
        st.success("API 키가 저장되었습니다!")
    
    st.divider()
    
    if st.button("🗑️ 대화 기록 지우기"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("### 📝 사용 방법")
    st.markdown("""
    1. API 키를 입력하고 저장하세요
    2. 메시지를 입력하고 전송하세요
    3. Gemini AI가 응답합니다
    """)

# 메인 화면
st.title("🤖 Gemini Chatbot")
st.markdown("Google Gemini API를 사용하는 챗봇 애플리케이션")

# 채팅 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    # API 키 확인
    if not st.session_state.api_key:
        st.error("⚠️ 먼저 API 키를 입력하고 저장해주세요!")
        st.stop()
    
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Gemini API 호출
    with st.chat_message("assistant"):
        with st.spinner("응답 생성 중..."):
            try:
                response = requests.post(
                    f"{API_ENDPOINT}?key={st.session_state.api_key}",
                    json={
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }]
                    },
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "응답을 받을 수 없습니다.")
                    
                    st.markdown(assistant_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    error_message = f"오류가 발생했습니다: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", error_message)
                    except:
                        pass
                    
                    st.error(f"❌ {error_message}")
                    st.session_state.messages.append({"role": "assistant", "content": f"오류: {error_message}"})
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ 네트워크 오류: {str(e)}")
            except Exception as e:
                st.error(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")

# 하단 정보
st.divider()
st.caption("💡 Tip: .env 파일에 GOOGLE_API_KEY를 설정하면 자동으로 불러옵니다.")

