import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import os

# 1. API 키 설정 (비밀번호)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("설정에서 API 키를 입력해주세요!")
    st.stop()

# 2. 화면 설정
st.set_page_config(page_title="4.우리 몸의 구조와 기능", page_icon="🩺")
st.title("4.우리 몸의 구조와 기능")
st.caption("선생님과 함께 우리 몸에 대해 재미있게 알아보아요!")

# 3. 모델 연결 (안전장치 강화: Flash 실패 시 Pro로 자동 전환)
@st.cache_resource
def get_model():
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # 시도할 모델 순서: 1.5 Flash (빠름) -> 1.5 Pro (똑똑함) -> Pro (구형, 안정적)
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    selected_model = None
    model_name_log = ""

    for model_name in candidate_models:
        try:
            # 모델 연결 시도
            temp_model = genai.GenerativeModel(model_name)
            # 테스트 발사 (진짜 되는지 확인)
            temp_model.generate_content("test")
            selected_model = temp_model
            model_name_log = model_name
            break # 성공하면 반복 중단
        except Exception:
            continue # 실패하면 다음 모델로 넘어감

    return selected_model, model_name_log

# 모델 불러오기 실행
model, connected_name = get_model()

if model is None:
    st.error("😭 모든 AI 모델 연결에 실패했어요. 잠시 후 다시 시도해주세요.")
    st.stop()
else:
    # 사이드바에 연결된 모델 표시
    st.sidebar.success(f"✅ 연결 성공! ({connected_name})")

# 4. 자료 읽기 함수
@st.cache_data(show_spinner=False)
def load_data():
    folder_path = 'data'
    combined_text = ""
    if not os.path.exists(folder_path): return ""
    
    files = os.listdir(folder_path)
    KEYWORDS = ["뼈", "근육", "소화", "심장", "호흡", "배설", "뇌", "신경"]

    for filename in files:
        path = os.path.join(folder_path, filename)
        try:
            content = ""
            if filename.endswith('.pdf'):
                with open(path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages: content += page.extract_text()
            elif filename.endswith('.docx'):
                doc = Document(path)
                for para in doc.paragraphs: content += para.text + "\n"
            elif filename.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f: content = f.read()
            
            if any(k in content for k in KEYWORDS):
                combined_text += f"\n[자료: {filename}]\n{content}"
        except: pass
    return combined_text[:50000]

# 5. 챗봇 본체
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕! 우리 몸에 대해 궁금한 게 있니? 선생님이 알려줄게! 😊"}]

# 자료 로딩
if "knowledge" not in st.session_state:
    st.session_state.knowledge = load_data()

# 화면에 대화 그리기
for msg in st.session_state.messages:
    icon = "🧑‍🏫" if msg["role"] == "assistant" else "🧑‍🎓"
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input("질문 입력..."):
    st.chat_message("user", avatar="🧑‍🎓").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 답변 생성
    with st.chat_message("assistant", avatar="🧑‍🏫"):
        box = st.empty()
        try:
            sys_prompt = f"""
            당신은 초등학교 6학년 과학 선생님입니다.
            지식: {st.session_state.knowledge}
            
            [규칙]
            1. 초등학생 눈높이로 쉽고 친절하게 설명하세요.
            2. 욕설, 폭력, 위험한 질문은 단호하게 거절하고 올바른 태도를 지도하세요.
            3. 틀린 내용을 말하면 정답을 바로 주지 말고, 힌트를 주어 스스로 생각하게 하세요.
            """
            
            full_prompt = sys_prompt + "\n학생: " + prompt
            response = model.generate_content(full_prompt, stream=True)
            
            full_text = ""
            for chunk in response:
                full_text += chunk.text
                box.markdown(full_text + "▌")
            box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            box.error(f"오류가 났어요: {e}")