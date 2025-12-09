def ask_gemini(user_input, movie_data, role):
    """Gemini에게 역할을 부여하고 대답하게 합니다."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 👇 여기를 'gemini-pro'로 변경했습니다.
        model = genai.GenerativeModel('gemini-pro')

        # AI에게 보낼 지령서(프롬프트) 작성
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
