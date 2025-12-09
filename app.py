import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta

# ==========================================
# 👇 사용자님의 API 키 (건드리지 마세요)
# ==========================================
GEMINI_API_KEY = "AIzaSyAeViQ5me2F19XOPv3VbzIq-nqB6Wwrggc"
KOBIS_API_KEY = "f6ae9fdbd8ba038eda177250d3e57b4c"
# ==========================================

st.set_page_config(page_title="나만의 영화 AI", page_icon="🎬")
st.title("🎬 나만의 AI 영화관 (Final)")

# --- 사이드바 ---
with st.sidebar:
    st.header("🎭 AI 페르소나")
    persona = st.selectbox(
        "대화 상대 선택",
        ["친절한 영화관 알바생", "냉철한 영화 평론가", "사극 말투 선비", "힙합 래퍼", "5살 조카"]
    )
    target_date = st.date_input("날짜 선택", datetime.now() - timedelta(days=1))

# --- 함수 ---
def get_box_office_data(date):
    dt_str = date.strftime("%Y%m%d")
    url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={KOBIS_API_KEY}&targetDt={dt_str}"
    try:
        response = requests.get(url)
        daily_list = response.json().get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
        if not daily_list: return "데이터 없음"
        
        text = ""
        for item in daily_list:
            text += f"[{item['rank']}위] {item['movieNm']} (관객: {item['audiAcc']}명)\n"
        return text
    except: return "통신 오류"

def ask_gemini(user_input, movie_data, role):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 👇 업데이트 후 가장 잘 작동하는 최신 모델
        model = genai.GenerativeModel('gemini-1.5-flash') 

        prompt = f"""
        역할: {role}
        정보: {movie_data}
        질문: {user_input}
        위 정보를 바탕으로 해당 역할의 말투로 대답해.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🚨 오류 발생: {e}\n\n(터미널에서 'pip install --upgrade google-generativeai'를 꼭 실행해주세요!)"

# --- 메인 ---
if 'data' not in st.session_state: st.session_state['data'] = ""

# 데이터 가져오기
if st.button("박스오피스 데이터 불러오기") or not st.session_state['data']:
    st.session_state['data'] = get_box_office_data(target_date)

# 채팅
if "msgs" not in st.session_state: st.session_state.msgs = []
for msg in st.session_state.msgs:
    st.chat_message(msg["role"]).markdown(msg["content"])

if prompt := st.chat_input("질문하세요"):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            res = ask_gemini(prompt, st.session_state['data'], persona)
            st.markdown(res)
            st.session_state.msgs.append({"role": "assistant", "content": res})
