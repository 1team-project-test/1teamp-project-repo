import streamlit as st
import json
import mariadb_control as db

def render_history_page():
    """🎯 과거 진행했던 AI 모의 면접 및 피드백 리포트 통합 복원 관리 화면"""
    st.subheader("🎯 나의 과거 면접 기록 관리")
    st.caption("MariaDB 데이터베이스에 안전하게 보관된 지원자님의 지난 면접 대화록 및 AI 평가서 히스토리입니다.")
    st.markdown("---")

    uid = st.session_state["user_info"]["user_id"]
    histories = db.get_user_interview_histories(uid)

    if not histories:
        st.info("ℹ️ 아직 저장된 과거 면접 이력이 존재하지 않습니다. 실전 면접방에서 첫 훈련을 완료해 보세요!")
        return

    col1, col2 = st.columns([1, 1.4], gap="large")

    with col1:
        st.markdown("##### 📅 면접 보관함 목록")
        options = []
        for h in histories:
            date_str = h["created_at"].strftime("%Y-%m-%d %H:%M")
            options.append("📌 [{}] {} - {}".format(date_str, h["company"], h["job"]))
            
        selected_option = st.radio("다시 읽어볼 면접 이력을 선택하세요", options, key="history_select_radio")
        selected_index = options.index(selected_option)
        selected_history = histories[selected_index]

    with col2:
        st.markdown("##### 💬 선택한 면접 내용 및 AI 평가서 복원")
        st.info("🧠 성향: **{}**".format(selected_history["interviewer_style"]))
        
        # 탭을 분리하여 대화록과 채점 리포트를 깔끔하게 교대 열람하도록 UI 정돈
        v_tab1, v_tab2 = st.tabs(["💬 당시 대화록 복원", "📊 당시 AI 피드백 복원"])
        
        with v_tab1:
            try:
                chat_logs = json.loads(selected_history["chat_log"])
                for msg in chat_logs:
                    with st.chat_message(msg["role"]): st.write(msg["content"])
            except: st.error("❌ 대화록 데이터를 복원하는 과정에서 오류가 발생했습니다.")
            
        with v_tab2:
            # 💡 [핵심 구현] 저장되어 있던 피드백 데이터가 존재하면 등급판과 아코디언까지 완벽 복원 가동
            if selected_history.get("feedback_log"):
                try:
                    f_report = json.loads(selected_history["feedback_log"])
                    
                    sc1, sc2 = st.columns(2)
                    with sc1: st.metric(label="💯 당시 채점 점수", value="{} / 100 점".format(f_report.get("total_score", 0)))
                    with sc2: st.metric(label="🏅 당시 합격 등급", value="[{}] 등급".format(f_report.get("grade", "B")))
                    st.markdown("---")
                    
                    with st.expander("✨ 당시 핵심 강점 (Strengths)", expanded=False):
                        st.success(f_report.get("strengths", "기록이 없습니다."))
                    with st.expander("⚠️ 당시 아쉬운 점 (Weaknesses)", expanded=False):
                        st.error(f_report.get("weaknesses", "기록이 없습니다."))
                    with st.expander("💡 면접관 제안 모범 답안 코칭", expanded=False):
                        st.info(f_report.get("best_answer_guide", "기록이 없습니다."))
                except: st.error("❌ 피드백 리포트 데이터를 파싱하는 중 오류가 발생했습니다.")
            else:
                st.warning("⚠️ 해당 면접 세션은 피드백 연산이 완료되기 전에 종료되어 리포트 기록이 보관되지 않았습니다.")