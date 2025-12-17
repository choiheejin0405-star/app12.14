import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import os

# 1. API 키 설정
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("설정에서 API 키를 입력해주세요!")
    st.stop()

# 2. 화면 설정
st.set_page_config(page_title="4.우리 몸의 구조와 기능", page_icon="🩺")
st.title("4.우리 몸의 구조와 기능")
st.caption("선생님과 함께 우리 몸에 대해 재미있게 알아보아요!")

# 3. 모델 연결 (선생님 요청: 사용 가능한 모델 직접 탐색 방식 ⭐)
@st.cache_resource
def get_model():
    genai.configure(api_key=GOOGLE_API_KEY)
    
    selected_model = None
    connected_name = ""
    
    try:
        # [핵심 기능] 내 계정에서 사용 가능한 모든 모델을 조회합니다.
        # "generateContent" (대화 기능)를 지원하는 놈들만 추려냅니다.
        my_available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                my_available_models.append(m)

        # 사용 가능한 모델이 하나도 없다면?
        if not my_available_models:
            return None, "사용 가능한 모델을 찾을 수 없음"

        # [똑똑한 선택 전략]
        # 조회된 목록(my_available_models) 중에서 가장 좋은 걸 순서대로 찾습니다.
        
        # 1순위: 1.5 Flash (빠르고 최신)
        for m in my_available_models:
            if 'gemini-1.5-flash' in m.name:
                selected_model = genai.GenerativeModel(m.name)
                connected_name = m.name
                break
        
        # 1순위가 없으면 -> 2순위: 1.5 Pro (똑똑함)
        if selected_model is None:
            for m in my_available_models:
                if 'gemini-1.5-pro' in m.name:
                    selected_model = genai.GenerativeModel(m.name)
                    connected_name = m.name
                    break
        
        # 2순위도 없으면 -> 3순위: 그냥 Gemini Pro
        if selected_model is None:
            for m in my_available_models:
                if 'gemini-pro' in m.name:
                    selected_model = genai.GenerativeModel(m.name)
                    connected_name = m.name
                    break
        
        # 아무것도 매칭이 안 되면 -> 그냥 목록의 첫 번째 놈을 무조건 잡습니다. (뭐라도 연결!)
        if selected_model is None:
            first_model = my_available_models[0]
            selected_model = genai.GenerativeModel(first_model.name)
            connected_name = f"{first_model.name} (자동 선택됨)"

    except Exception as e:
        return None, str(e)

    return selected_model, connected_name

# 모델 불러오기 실행
model, model_name = get_model()

if model is None:
    st.error(f"😭 모델 연결 실패: {model_name}\nAPI 키를 다시 확인하거나 잠시 후 시도해주세요.")
    st.stop()
else:
    # 성공하면 어떤 모델을 찾았는지 사이드바에 표시
    st.sidebar.success(f"✅ 내 컴퓨터 맞춤 연결!\n모델명: {model_name}")

# 4. 자료 자동 읽기 함수
@st.cache_data(show_spinner=False)
def load_data():
    folder_path = 'data'
    combined_text = ""
    
    if not os.path.exists(folder_path):
        return ""

    files = os.listdir(folder_path)
    KEYWORDS = ["뼈", "근육", "소화", "심장", "호흡", "배설", "뇌", "신경", "감각"]

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            content = ""
            if filename.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        content += page.extract_text()
            elif filename.endswith('.docx'):
                doc = Document(file_path)
                for para in doc.paragraphs:
                    content += para.text + "\n"
            elif filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            if any(k in content for k in KEYWORDS):
                combined_text += f"\n\n--- [참고 자료: {filename}] ---\n{content}"
        except Exception:
            pass 

    if len(combined_text) > 60000:
        combined_text = combined_text[:60000] + "\n...(이하 생략)..."
        
    return combined_text

# 5. 시스템 프롬프트 (교육 및 윤리 기능 완비)
if "knowledge" not in st.session_state:
    with st.spinner("선생님이 자료를 챙겨오고 있어요... 📚"):
        st.session_state.knowledge = load_data()

system_prompt = f"""
당신은 초등학교 6학년 과학 선생님(이모지: 🧑‍🏫)입니다.
아래 [학습 자료]의 지식을 바탕으로 학생과 대화합니다.

[학습 자료]:
{st.session_state.knowledge}

[⚠️ 중요: 윤리 및 안전 가이드라인 (보안관 기능)]:
1. **비속어 및 비방 금지**: 학생이 욕설, 비속어, 친구를 놀리는 말을 쓰면 정중하지만 단호하게 답변을 거절하고 바른 말을 쓰도록 지도하세요.
2. **위험한 질문 차단**: 폭발물 제조, 자해, 폭력, 약물 오남용 등 위험하거나 비윤리적인 질문에는 **절대 답하지 마세요.**
3. **대처 방법**: "그런 위험한 행동은 하면 안 돼.", "우리 과학 수업과 관련 없는 비윤리적인 내용은 알려줄 수 없어."라고 말하고, 다시 우리 몸에 대한 학습 주제로 대화를 유도하세요.
4. **개인정보 보호**: 학생이 본인의 이름, 주소, 전화번호를 말하려 하면 "개인정보는 소중하니까 여기에 적으면 안 돼!"라고 알려주세요.

[교육적 대화 및 행동 수칙]:
1. **말투**: 다정하고 친절한 존댓말(해요체) 사용. 적절한 이모지 사용으로 친밀감 형성.
2. **눈높이 설명**: 어려운 전문 용어 대신 쉬운 비유를 사용하세요. (예: 심장 -> 펌프, 혈관 -> 도로)
3. **오개념 교정**: 학생이 틀린 내용을 말하면 바로 정답을 주지 말고, 반례를 들거나 질문을 던져 스스로 깨닫게 유도하세요.
4. **단계적 힌트(비계 설정)**: 퀴즈나 질문에 대해 학생이 모를 경우, 힌트를 단계적으로 제공하여 사고력을 키워주세요.
5. **질문 유도**: 설명이 끝난 후에는 "혹시 더 궁금한 게 있니?" 또는 관련된 흥미로운 질문을 던져 대화를 이어가세요.
"""

# 6. 대화 처리
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕! 반가워. 선생님이랑 우리 몸에 대해 재미있게 이야기 나눠볼까? 혹시 궁금한 점이 있니? 😊"}
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
            msg_box.error(f"답변을 만드는 중 문제가 생겼어요: {e}")