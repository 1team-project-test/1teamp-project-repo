import streamlit as st
from db_handler import save_message, get_chat_history, save_feedback

st.title("💬 AI 면접관의 꼬리질문방")

# 설정 확인
if not st.session_state.get("job_title") or not st.session_state.get("resume_text"):
    st.warning("먼저 '1_Setting' 페이지에서 직무와 이력서를 입력해 주세요.")
    st.stop()

st.caption(f"현재 설정된 직무: **{st.session_state.job_title}**")

# DB에서 과거 대화 기록 불러오기 (혹은 세션 관리)
chat_history = get_chat_history()

# 첫 방문 시 면접관의 첫 질문 자동 생성 뼈대
if len(chat_history) == 0:
    first_question = f"안녕하세요. {st.session_state.job_title} 직무에 지원하신 이유를 간단히 말씀해 주세요."
    save_message("assistant", first_question)
    st.rerun()

# 대화 기록 화면에 출력
for chat in chat_history:
    if chat['role'] == "user":
        with st.chat_message("user"):
            st.write(chat['message'])
    else:
        with st.chat_message("assistant"):
            st.write(chat['message'])

# 사용자 입력 받기
if user_input := st.chat_input("답변을 입력하세요..."):
    # 1. 사용자 답변 화면 출력 및 DB 저장
    with st.chat_message("user"):
        st.write(user_input)
    save_message("user", user_input)
    
    # 2. AI의 꼬리질문 생성 로직 뼈대 (현재는 임시 텍스트)
    # TODO: 여기에 LLM API를 연동하여 st.session_state.resume_text와 user_input을 분석하는 프롬프트를 넣어야 합니다.
    ai_follow_up = f"방금 말씀하신 '{user_input[:15]}...' 관련 기술에 대해 구체적으로 어떻게 기여할 수 있는지 꼬리질문 드립니다."
    
    # 3. AI 답변 화면 출력 및 DB 저장
    with st.chat_message("assistant"):
        st.write(ai_follow_up)
    save_message("assistant", ai_follow_up)
    
    st.rerun()

st.write("---")
col1, col2 = st.columns([4, 1])

with col2:
    if st.button("🏁 면접 종료 및 피드백", use_container_width=True):
        with st.spinner("AI 면접관이 답변을 종합하여 분석 리포트를 작성 중입니다..."):
            
            # TODO: 실제 구현 시에는 chat_history 전체를 긁어 LLM API에 전달하여 분석 결과를 받아와야 합니다.
            # 지금은 임시 데이터(Mock Data)를 DB에 저장합니다.
            mock_score = 85
            mock_good = "- 직무와 관련된 핵심 프로젝트 경험을 구체적인 수치(예: 성능 20% 개선)를 들어 신뢰감 있게 답변함.\n- 꼬리질문에도 당황하지 않고 본인의 논리를 차분하게 유지함."
            mock_bad = "- 특정 기술 스택을 선택한 이유를 설명할 때, '그냥 많이 써서' 식의 모호한 답변이 아쉬움.\n- 긴장으로 인해 문장의 끝맺음이 흐려지는 경향이 있음."
            mock_tips = "1. 대답 시 두괄식 기법(결론부터 말하기)을 조금 더 적극적으로 활용해 보세요.\n2. 본인이 사용한 오픈소스 라이브러리의 내부 동작 원리를 1분 내외로 요약하는 연습이 필요합니다."
            
            # DB에 피드백 결과 저장
            save_feedback(st.session_state.job_title, mock_score, mock_good, mock_bad, mock_tips)
            
            st.success("리포트 작성 완료! '3_Feedback' 페이지로 자동 이동합니다.")
            st.switch_page("pages/3_Feedback.py") # 피드백 페이지로 이동

    