import json
import streamlit as st
from local_llm import ask_local_ai

def generate_interview_feedback(history_messages):
    """Ollama 기반 AI 면접 종합 평가"""
    try:
        conversation_log = ""

        for msg in history_messages:
            if msg["role"] == "assistant":
                conversation_log += f"면접관: {msg['content']}\n"
            elif msg["role"] == "user":
                conversation_log += f"지원자: {msg['content']}\n"

        prompt = f"""
너는 15년 경력의 채용 담당자이자 면접 평가 전문가이다.

아래 면접 대화 내용을 분석하여 반드시 JSON 형식으로만 답변하라.

반드시 아래 형식을 지켜라.

{{
    "total_score": 점수,
    "grade": "등급",
    "strengths": "강점",
    "weaknesses": "약점",
    "best_answer_guide": "코칭"
}}

평가 기준:
- 논리성
- 직무 적합성
- 문제 해결 능력
- 의사소통 능력
- 경험의 구체성
- 답변의 신뢰성

등급 기준:
90~100 = S
80~89 = A
70~79 = B
60~69 = C
59 이하 = D

면접 대화:

{conversation_log}

JSON만 출력하라.
"""

        result = ask_local_ai(prompt)

        # ```json 제거
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        return json.loads(result)

    except Exception as e:
        print(f"[OLLAMA FEEDBACK ERROR] {e}")
        return None

def render_feedback_page():
    """📊 AI 면접 종합 피드백 & 채점 리포트 화면"""
    
    st.subheader("📊 AI 면접 채점 및 종합 피드백 리포트")
    st.caption("진행하신 실전 압박 면접 대화 이력을 바탕으로 AI 채용 전문가가 도출한 역량 평가서입니다.")
    st.markdown("---")

    # 1. 예외 방어: 대화 기록 세션이 존재하지 않으면 차단
    if "interview_messages" not in st.session_state or len(st.session_state["interview_messages"]) <= 2:
        st.warning("⚠️ 충분한 면접 대화 기록이 존재하지 않습니다. 면접방에서 먼저 면접을 진행해 주세요.")
        if st.button("🤖 면접방으로 돌아가기"):
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
        return

    # 2. 리포트 생성 가동 및 캐싱 (중복 API 호출 방어)
    if "feedback_report" not in st.session_state:
        with st.spinner("🧠 AI 전문가가 대화 이력을 정밀 스캔하여 종합 리포트를 작성하는 중입니다..."):
            report = generate_interview_feedback(st.session_state["interview_messages"])
            if report:
                st.session_state["feedback_report"] = report
            else:
                st.error("⚠️ AI 피드백 생성에 실패했습니다. 터미널 오류를 확인해 주세요.")
                return

    report = st.session_state["feedback_report"]

    # 3. 최상단 스코어 보드 레이아웃 시각화
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="💯 종합 채점 점수", value=f"{report.get('total_score', 0)} / 100 점")
    with col2:
        st.metric(label="🏅 예상 합격 등급", value=f"[{report.get('grade', 'B')}] 등급")

    st.markdown("---")

    # 4. 아코디언 스타일을 활용한 가독성 높은 상세 항목 가시화
    with st.expander("✨ 지원자님의 핵심 강점 (Strengths)", expanded=True):
        st.success(report.get("strengths", "분석된 내용이 없습니다."))

    with st.expander("⚠️ 아쉬운 점 및 취약점 (Weaknesses)", expanded=True):
        st.error(report.get("weaknesses", "분석된 내용이 없습니다."))

    with st.expander("💡 면접관이 제안하는 핵심 모범 답안 가이드 (Coaching)", expanded=True):
        st.info(report.get("best_answer_guide", "분석된 내용이 없습니다."))

    st.markdown("---")

    # 5. 새 면접 준비를 위한 세션 리셋 제어 구역
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🔄 이 서류로 면접 다시 도전하기", use_container_width=True):
            st.session_state.pop("interview_messages", None)
            st.session_state.pop("feedback_report", None)
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
            
    with btn_col2:
        if st.button("📄 새로운 서류 제출하러 가기", use_container_width=True, type="primary"):
            for key in ["document_loaded", "db_data_fetched", "selected_company", "selected_job", "resume_text", "intro_text", "document_text", "interview_messages", "feedback_report"]:
                st.session_state.pop(key, None)
            st.session_state["current_menu"] = "📄 이력서 제출"
            st.rerun()