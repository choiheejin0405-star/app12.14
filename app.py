import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import os

# ==========================================
# [선생님 비밀 설정 구역]
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("설정에서 API 키를 입력해주세요!")
    st.stop()
# ==========================================

# 1. 화면 설정
st.set_page_config(page_title="4.우리 몸의 구조와 기능", page_icon="🩺")
st.title("4.우리 몸의 구조와 기능")
st.caption("선생님과 함께 우리 몸에 대해 재미있게 알아보아요!")

# 2. 자료 자동 읽기 함수
@st.cache_data(show_spinner=False)
def load_data_from_folder():
    folder_path = 'data'
    combined_text = ""
    
    if not os.path.exists(folder_path):
        return None

    files = os.listdir(folder_path)
    if not files:
        return None

    KEYWORDS = [
        "뼈", "근육", "소화", "입", "식도", "위", "창자", "항문", "영양소",
        "호흡", "숨", "폐", "허파", "산소", "이산화 탄소",
        "순환", "심장", "혈관", "혈액", "맥박",
        "배설", "콩팥", "오줌", "방광", "노폐물",
        "자극", "반응", "신경", "뇌", "척수", "감각"
    ]

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            if filename.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text and any(keyword in text for keyword in KEYWORDS):
                            combined_text += f"\n\n--- [참고 자료: {filename}] ---\n{text}"
            elif filename.endswith('.docx'):
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text = para.text
                    if any(keyword in text for keyword in KEYWORDS):
                         combined_text += text + "\n"
            elif filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    combined_text += text
        except Exception:
            pass 

    if len(combined_text) > 50000:
        combined_text = combined_text[:50000]
        combined_text += "\n...(내용이 많아 요약됨)..."
        
    return combined_text

# 3. 모델 자동 검색 및 연결 (안전장치 강화됨 ⭐)
if not GOOGLE_API_KEY:
    st.error("🚨 선생님! 코드 윗부분에 API 키를 입력해주세요.")
    st.stop()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # 우선순위: 1.5 Flash -> 1.5 Pro -> Pro (구형이지만 안정적)
    target_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
    model = None
    connected_model_name = ""

    # 1. 내가 원하는 모델 순서대로 연결 시도
    for target in target_models:
        try:
            temp_model = genai.GenerativeModel(target)
            temp_model.generate_content("test") # 테스트 발사
            model = temp_model
            connected_model_name = target
            break
        except Exception:
            continue
    
    # 2. 다 실패하면, 진짜 아무거나 잡히는 거 연결 (구조 요청)
    if model is None:
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # 'vision' 같은 특수 모델 제외하고 텍스트 되는 것 찾기
                    if 'gemini' in m.name:
                        model = genai.GenerativeModel(m.name)
                        connected_model_name = f"{m.name} (비상연결)"
                        break
        except:
            pass

    # 3. 그래도 없으면 에러 표시
    if model is None:
        st.error("😭 연결 가능한 AI 모델을 찾을 수 없어요. 잠시 후 다시 시도하거나 API 키를 확인해주세요.")
        st.stop()
    else:
        st.sidebar.success(f"✅ 연결됨: {connected_model_name}")

    # 자료 읽기 시작
    if "local_knowledge" not in st.session_state:
        with st.spinner("선생님이 자료를 준비하고 있어요... 잠시만요! 📚"):
            data = load_data_from_folder()
            if data:
                st.session_state.local_knowledge = data
            else:
                st.session_state.local_knowledge = ""
                st.warning("⚠️ 'data' 폴더가 비어있거나 없어요. 챗봇이 기본 지식으로만 대답합니다.")

except Exception as e:
    st.error(f"초기 설정 오류: {e}")
    st.stop()

# 4. 시스템 프롬프트 (윤리 규정 포함)
system_prompt = f"""
당신은 초등학교 6학년 과학 선생님(이모지: 🧑‍🏫)입니다.
아래 [학습 자료]의 지식을 바탕으로 학생과 대화합니다.

[학습 자료]:
{st.session_state.local_knowledge}

[⚠️ 중요: 윤리 및 안전 가이드라인]:
1. **비속어 및 비방 금지**: 학생이 욕설, 비속어, 친구를 놀리는 말을 쓰면 정중하지만 단호하게 답변을 거절하고 바른 말을 쓰도록 지도하세요.
2. **위험한 질문 차단**: 폭발물 제조, 자해, 폭력, 약물 오남용 등 위험하거나 비윤리적인 질문에는 **절대 답하지 마세요.**
3. **대처 방법**: "그런 위험한 행동은 하면 안 돼.", "우리 과학 수업과 관련 없는 비윤리적인 내용은 알려줄 수 없어."라고 말하고, 다시 우리 몸에 대한 학습 주제로 대화를 유도하세요.
4. **개인정보 보호**: 학생이 본인의 이름, 주소, 전화번호를 말하려 하면 "개인정보는 소중하니까 여기에 적으면 안 돼!"라고 알려주세요.

[대화 및 행동 수칙]:
1. **말투**: 다정하고 친절한 존댓말(해요체) 사용. 이모지 적절히 사용.
2. **설명**: 쉬운 말로 풀어서 이야기하듯 설명(비계 설정). 질문에 대한 답만 하지 말고 원리를 설명할 것.
3. **오개념 교정**: 학생이 틀리면 반례를 들어 스스로 깨닫게 유도. 절대 그냥 넘어가지 말 것.
4. **출처 언급 금지**: "자료에 따르면" 같은 말 금지.
5. **질문**: 한 번에 하나씩만 질문하여 사고 확장 유도.
"""

# 5. 대화 처리
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕! 반가워. 선생님이랑 우리 몸에 대해 재미있게 이야기 나눠볼까? 혹시 궁금한 과학 이야기가 있니? 😊"}
    ]

for message in st.session_state.messages:
    avatar = "🧑‍🏫" if message["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("질문이나 대답을 입력하세요"):
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🧑‍🏫"):
        msg_box = st.empty()
        try:
            full_prompt = system_prompt + f"\n\n학생 말: {prompt}"
            response = model.generate_content(full_prompt, stream=True)
            full_response = ""
            for chunk in response:
                full_response += chunk.text
                msg_box.markdown(full_response + "▌")
            msg_box.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})     
        except Exception as e:
            msg_box.error(f"답변 생성 중 오류: {e}")