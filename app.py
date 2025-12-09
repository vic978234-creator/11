import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta

# ==========================================
# 👇 API 키 설정
# ==========================================
GEMINI_API_KEY = "AIzaSyAeViQ5me2F19XOPv3VbzIq-nqB6Wwrggc"
KOBIS_API_KEY = "f6ae9fdbd8ba038eda177250d3e57b4c"
# ==========================================

st.set_page_config(page_title="영화 AI (자동복구모드)", page_icon="🚑")

st.title("🚑 AI 영화관 (자동 모델 감지)")
st.caption("오류 해결을 위해 사용 가능한 AI 모델을 자동으로 찾습니다.")

# --- 1. 사용 가능한 모델 찾기 함수 (핵심) ---
def find_working_model(api_key):
    """API 키를 이용해 현재 사용 가능한 모델 이름을 찾아냅니다."""
    try:
        genai.configure(api_key=api_key)
        
        # 사용 가능한 모델 목록 조회
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 1순위: Flash (빠름), 2순위: Pro (안정적), 3순위: 아무거나
        if 'models/gemini-1.5-flash' in available_models:
            return 'gemini-1.5-flash', available_models
        elif 'models/gemini-pro' in available_models:
            return 'gemini-pro', available_models
        elif len(available_models) > 0:
            # 모델 이름 앞에 'models/'가 붙어있으면 떼고 반환 시도
            return available_models[0].replace('models/', ''), available_models
        else:
            return None, []
    except Exception as e:
        return None, str(e)

# --- 2. 박스오피스 데이터 함수 ---
def get_box_office_data(date):
    dt_str = date.strftime("%Y%m%d")
    url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={KOBIS_API_KEY}&targetDt={dt_str}"
    try:
        response = requests.get(url)
        data = response.json()
        daily_list = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
        if not daily_list: return "데이터 없음"
        text = ""
        for item in daily_list:
            text += f"[{item['rank']}위] {item['movieNm']} (관객: {item['audiAcc']}명)\n"
        return text
    except: return "통신 오류"

# --- 3. Gemini 대화 함수 ---
def ask_gemini(model_name, user_input, movie_data, role):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        prompt = f"역할: {role}\n정보: {movie_data}\n질문: {user_input}\n위 정보로 대답해."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"에러 발생: {e}"

# --- 메인 실행 로직 ---

# 사이드바에서 모델 상태 진단
with st.sidebar:
    st.header("🛠️ 시스템 진단")
    
    # 모델 찾기 실행
    target_model, all_models = find_working_model(GEMINI_API_KEY)
    
    if target_model:
        st.success(f"연결 성공! \n사용 모델: {target_model}")
        with st.expander("전체 모델 목록 보기"):
            st.write(all_models)
    else:
        st.error("사용 가능한 모델을 찾을 수 없습니다.")
        st.error(f"오류 내용: {all_models}") # 에러 메시지 출력
        st.warning("터미널에서 'python -m pip install --upgrade google-generativeai'를 실행하세요.")

    st.divider()
    persona = st.selectbox("말투 선택", ["친절한 알바생", "평론가", "선비"])
    target_date = st.date_input("날짜", datetime.now() - timedelta(days=1))

# 메인 화면
if 'data' not in st.session_state: st.session_state['data'] = ""

# 데이터 로드
if st.button("데이터 가져오기") or not st.session_state['data']:
    st.session_state['data'] = get_box_office_data(target_date)

# 채팅창
if "msgs" not in st.session_state: st.session_state.msgs = []
for msg in st.session_state.msgs:
    st.chat_message(msg["role"]).markdown(msg["content"])

if prompt := st.chat_input("질문하세요"):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        if not target_model:
            st.error("AI 모델을 찾지 못해 대답할 수 없습니다. 사이드바의 오류를 확인하세요.")
        else:
            with st.spinner(f"({target_model} 모델이 생각 중...)"):
                res = ask_gemini(target_model, prompt, st.session_state['data'], persona)
                st.markdown(res)
                st.session_state.msgs.append({"role": "assistant", "content": res})
