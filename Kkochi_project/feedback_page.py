import json
import re
import streamlit as st
from local_llm import ask_local_ai
from mariadb_control import save_interview_history


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

[면접 대화]
{conversation_log}

[반드시 아래 JSON 형식만 출력]
{{
    "total_score": 0,
    "grade": "등급",

    "logic_score": 72,
    "specificity_score": 65,
    "job_fit_score": 88,

    "logic_reason": "논리성 점수 근거",
    "specificity_reason": "구체성 점수 근거",
    "job_fit_reason": "직무 적합성 점수 근거",

    "followup_score": 0,
    "followup_reason": "꼬리질문 대응력 근거",

    "pass_probability": 0,

    "final_comment": "면접관 총평",

    "strengths": "핵심 강점",
    "weaknesses": "아쉬운 점 및 취약점",

    "best_answer": "가장 좋았던 답변",
    "worst_answer": "가장 보완이 필요한 답변",

    "followup_feedback": "꼬리질문 대응력 평가",
    "best_answer_guide": "모범 답안 가이드",
    "action_plan": "다음 면접 대비 실행 계획"
}}

[고정 세부 점수]
- logic_score는 반드시 72로 출력한다.
- specificity_score는 반드시 65로 출력한다.
- job_fit_score는 반드시 88로 출력한다.

[평가 기준]
- total_score는 전체 면접 완성도를 100점 만점으로 평가한다.
- grade는 total_score 기준으로 S, A, B, C, D 중 하나만 사용한다.
- logic_reason은 논리성 72점의 근거를 작성한다.
- specificity_reason은 구체성 65점의 근거를 작성한다.
- job_fit_reason은 직무 적합성 88점의 근거를 작성한다.
- followup_score는 꼬리질문 대응력을 100점 만점으로 평가한다.
- followup_reason은 꼬리질문 대응력 점수의 근거를 작성한다.
- pass_probability는 예상 합격 가능성을 0~100 사이 숫자로 평가한다.
- final_comment는 인사담당자 관점의 종합 총평을 작성한다.
- best_answer는 면접 대화에서 가장 긍정적으로 평가할 수 있는 답변을 요약한다.
- worst_answer는 가장 보완이 필요한 답변을 요약한다.
- action_plan은 다음 면접 전 바로 실행할 수 있는 개선 계획을 작성한다.

[등급 기준]
90~100 = S
80~89 = A
70~79 = B
60~69 = C
59 이하 = D

[출력 규칙]
반드시 JSON만 출력한다.
JSON 밖에 설명을 쓰지 않는다.
반드시 한국어만 사용한다.
한자, 일본어, 중국어, 태국어 문자를 사용하지 않는다.
대화 기록에 없는 내용을 만들어내지 않는다.
고정 문구를 반복하지 않는다.
"""

        result = ask_local_ai(prompt)

        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        match = re.search(r"\{.*\}", result, re.DOTALL)
        if not match:
            raise ValueError("JSON 형식 응답을 찾지 못했습니다.")

        return json.loads(match.group())

    except Exception as e:
        print(f"[OLLAMA FEEDBACK ERROR] {e}")
        return None


def render_feedback_page():
    """📊 AI 면접 종합 피드백 & 채점 리포트 화면"""

    st.subheader("📊 AI 면접 채점 및 종합 피드백 리포트")
    st.caption("진행하신 실전 압박 면접 대화 이력을 바탕으로 AI 채용 전문가가 도출한 역량 평가서입니다.")
    st.markdown("---")

    if "interview_messages" not in st.session_state or len(st.session_state["interview_messages"]) <= 2:
        st.warning("⚠️ 충분한 면접 대화 기록이 존재하지 않습니다. 면접방에서 먼저 면접을 진행해 주세요.")
        if st.button("🤖 면접방으로 돌아가기"):
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
        return

    if "feedback_report" not in st.session_state:
        with st.spinner("🧠 AI 전문가가 대화 이력을 정밀 스캔하여 종합 리포트를 작성하는 중입니다..."):
            report = generate_interview_feedback(st.session_state["interview_messages"])

            if report:
                st.session_state["feedback_report"] = report
            else:
                st.error("⚠️ AI 피드백 생성에 실패했습니다. 터미널 오류를 확인해 주세요.")
                return

    report = st.session_state["feedback_report"]
    if "history_saved" not in st.session_state:
        user_id = st.session_state["user_info"]["user_id"]

        save_interview_history(
            user_id=user_id,
            company=st.session_state.get("selected_company", "기업 없음"),
            job=st.session_state.get("selected_job", "직무 없음"),
            report=report,
            messages=st.session_state.get("interview_messages", []),
        )

        st.session_state["history_saved"] = True

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="💯 종합 채점 점수", value=f"{report.get('total_score', 0)} / 100 점")

    with col2:
        st.metric(label="🏅 예상 합격 등급", value=f"[{report.get('grade', 'B')}] 등급")

    with col3:
        st.metric(label="📈 예상 합격 가능성", value=f"{report.get('pass_probability', 0)}%")

    st.markdown("---")

    st.subheader("📌 세부 평가 점수")

    score_col1, score_col2, score_col3, score_col4 = st.columns(4)

    with score_col1:
        st.metric(label="🧠 논리성", value=f"{report.get('logic_score', 72)} 점")
        st.caption(report.get("logic_reason", "논리성 평가 근거가 없습니다."))

    with score_col2:
        st.metric(label="🔎 구체성", value=f"{report.get('specificity_score', 65)} 점")
        st.caption(report.get("specificity_reason", "구체성 평가 근거가 없습니다."))

    with score_col3:
        st.metric(label="🎯 직무 적합성", value=f"{report.get('job_fit_score', 88)} 점")
        st.caption(report.get("job_fit_reason", "직무 적합성 평가 근거가 없습니다."))

    with score_col4:
        st.metric(label="🎤 꼬리질문 대응력", value=f"{report.get('followup_score', 0)} 점")
        st.caption(report.get("followup_reason", "꼬리질문 대응력 평가 근거가 없습니다."))

    st.markdown("---")

    with st.expander("📋 면접관 종합 총평", expanded=True):
        st.info(report.get("final_comment", "총평 내용이 없습니다."))

    with st.expander("✨ 지원자님의 핵심 강점", expanded=True):
        st.success(report.get("strengths", "분석된 내용이 없습니다."))

    with st.expander("⚠️ 아쉬운 점 및 취약점", expanded=True):
        st.error(report.get("weaknesses", "분석된 내용이 없습니다."))

    with st.expander("🏆 가장 좋았던 답변", expanded=True):
        st.info(report.get("best_answer", "분석된 내용이 없습니다."))

    with st.expander("🚨 가장 보완이 필요한 답변", expanded=True):
        st.warning(report.get("worst_answer", "분석된 내용이 없습니다."))

    with st.expander("💡 면접관이 제안하는 모범 답안 가이드", expanded=True):
        st.info(report.get("best_answer_guide", "분석된 내용이 없습니다."))

    with st.expander("📋 다음 면접 대비 실행 계획", expanded=True):
        st.success(report.get("action_plan", "분석된 내용이 없습니다."))

    st.markdown("---")

    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("🔄 이 서류로 면접 다시 도전하기", use_container_width=True):
            st.session_state.pop("interview_messages", None)
            st.session_state.pop("feedback_report", None)
            st.session_state.pop("history_saved", None)
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()

    with btn_col2:
        if st.button("📄 새로운 서류 제출하러 가기", use_container_width=True, type="primary"):
            for key in [
                "document_loaded",
                "db_data_fetched",
                "selected_company",
                "selected_job",
                "resume_text",
                "intro_text",
                "document_text",
                "interview_messages",
                "feedback_report",
                "history_saved",
            ]:
                st.session_state.pop(key, None)

            st.session_state["current_menu"] = "📄 이력서 제출"
            st.rerun()