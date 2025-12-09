import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta

# ==========================================
# 👇 새로 알려주신 키로 교체했습니다.
# ==========================================
GEMINI_API_KEY = "AIzaSyAeViQ5me2F19XOPv3VbzIq-nqB6Wwrggc"
KOBIS_API_KEY = "f6ae9fdbd8ba038eda177250d3e57b4c"
# ==========================================

# --- 페이지 설정 ---
st.set_page_config(page_title="나만의 영화 AI", page_icon="🎬")

st.title("🎬 나만의 AI 영화관 (API 내장형)")
st.caption("새로운 Gemini API 키가 적용되었습니다.")

# --- 사이드바: 설정 ---
with st.sidebar:
    st.header("🎭 AI 페르소나(말투)")
    persona = st.selectbox(
        "누구와 대화하시겠어요?",
        ["친절한 영화관 알바생", "냉철한 영화 평론가", "사극 말투의 선비", "힙합 래퍼", "귀여운 5살 조카"]
    )
    
    st.divider()
    
    # 날짜 선택 (기본값: 어제)
    target_date = st.date_input("박스오피스 날짜", datetime.now() - timedelta(days=1))
    st.caption("※ 오늘 날짜는 집계 중이라 데이터가 없을 수 있어 어제가 기본값입니다.")

# --- 기능 함수 (순수 파이썬) ---

def get_box_office_data(date):
    """KOBIS API에서 영화 순위를 가져와 문자열로 정리합니다."""
    dt_str = date.strftime("%Y%m%d")
    url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={KOBIS_API_KEY}&targetDt={dt_str}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        result_dict = data.get('boxOfficeResult', {})
        daily_list = result_dict.get('dailyBoxOfficeList', [])
        
        if not daily_list:
            return "❌ 해당 날짜의 데이터가 없습니다. (미래 날짜이거나 API 오류일 수 있습니다.)"

        info_text = ""
        for item in daily_list:
            rank = item['rank']
            title = item['movieNm']
            open_date = item['openDt']
            audi_acc = item['audiAcc']
            
            info_text += f"[{rank}위] {title} (개봉: {open_date}, 누적관객: {audi_acc}명)\n"
            
        return info_text

    except Exception as e:
        return f"데이터 통신 중 오류 발생: {e}"

def ask_gemini(user_input, movie_data, role):
    """Gemini에게 역할을 부여하고 대답하게 합니다."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 👇 오류 방지를 위해 'gemini-pro' 모델로 설정했습니다.
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        당신은 '{role}'입니다. 아래 영화 데이터를 참고해서 사용자와 대화해주세요.
        
        [현재 박스오피스 데이터]
        {movie_data}
        
        [사용자 질문]
        {user_input}
        
        지침:
        1. 데이터에 있는 사실(순위, 관객수 등)은 정확히 말하세요.
        2. 영화의 줄거리나 재미 요소는 당신의 지식(AI)을 활용해서 풍부하게 설명하세요.
        3. 반드시 '{role}'의 말투와 성격을 끝까지 유지하세요.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 응답 오류: {e} (API 키를 확인해주세요)"

# --- 메인 화면 로직 ---

# 1. 영화 데이터 불러오기 (세션 캐싱)
cache_key = f"boxoffice_{target_date}"

if cache_key not in st.session_state:
    with st.spinner(f"{target_date} 영화 순위를 가져오는 중..."):
        data_text = get_box_office_data(target_date)
        st.session_state[cache_key] = data_text
        st.session_state['current_data'] = data_text

# 2. 채팅 인터페이스
st.subheader(f"💬 {persona}와의 대화")

# 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 내용 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 3. 사용자 입력 및 답변 처리
if prompt := st.chat_input("질문을 입력하세요 (예: 1위 영화 재밌어?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"{persona}가 답변을 생각 중입니다..."):
            ai_response = ask_gemini(
                prompt, 
                st.session_state.get('current_data', ''), 
                persona
            )
            st.markdown(ai_response)
    
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

# 데이터 확인용
with st.expander("참고: AI가 보고 있는 데이터 원본"):
    st.text(st.session_state.get('current_data', '데이터 없음'))
