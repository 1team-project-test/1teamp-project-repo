import json
import streamlit as st
from mariadb_control import get_interview_history


def render_history_page():
    st.subheader("📚 면접 이력")
    st.caption("이전에 진행한 면접 기록과 피드백 결과를 확인할 수 있습니다.")
    st.markdown("---")

    user_id = st.session_state["user_info"]["user_id"]
    histories = get_interview_history(user_id)

    if not histories:
        st.info("아직 저장된 면접 이력이 없습니다.")
        return

    total_count = len(histories)
    scores = [h.get("score", 0) for h in histories]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    best_score = max(scores) if scores else 0
    latest_score = scores[0] if scores else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("누적 면접 횟수", f"{total_count}회")
    with col2:
        st.metric("평균 점수", f"{avg_score}점")
    with col3:
        st.metric("최고 점수", f"{best_score}점")
    with col4:
        st.metric("최근 점수", f"{latest_score}점")

    st.markdown("---")

    for history in histories:
        created_at = history.get("created_at", "날짜 없음")
        title = f"{created_at} | {history.get('company', '기업 없음')} | {history.get('job', '직무 없음')} | {history.get('score', 0)}점"

        with st.expander(title):
            st.write(f"**등급:** {history.get('grade', '-')}")
            st.write(f"**논리성:** {history.get('logic_score', 0)}점")
            st.write(f"**구체성:** {history.get('specificity_score', 0)}점")
            st.write(f"**직무 적합성:** {history.get('job_fit_score', 0)}점")
            st.write(f"**꼬리질문 대응력:** {history.get('followup_score', 0)}점")
            st.write(f"**예상 합격 가능성:** {history.get('pass_probability', 0)}%")

            messages = json.loads(history.get("messages_json") or "[]")
            feedback = json.loads(history.get("feedback_json") or "{}")

            st.markdown("### 💬 면접 대화 기록")
            for msg in messages:
                if msg.get("role") == "system":
                    continue

                role = "면접관" if msg.get("role") == "assistant" else "지원자"
                st.markdown(f"**{role}**")
                st.write(msg.get("content", ""))

            st.markdown("### 📊 피드백 요약")
            st.success(feedback.get("strengths", "강점 기록 없음"))
            st.error(feedback.get("weaknesses", "약점 기록 없음"))
            st.info(feedback.get("action_plan", "실행 계획 없음"))