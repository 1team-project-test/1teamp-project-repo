import streamlit as st
import json
import mariadb_control as db

def render_history_page():
    """🎯 과거 진행했던 AI 모의 면접 및 피드백 리포트 통합 복원 및 삭제 관리 화면"""
    st.subheader("🎯 나의 과거 면접 기록 관리")
    st.caption("MariaDB 데이터베이스에 안전하게 보관된 지원자님의 지난 면접 대화록 및 AI 평가서 히스토리입니다.")
    st.markdown("---")

    # 로그인된 사용자 ID 가져오기
    if "user_info" not in st.session_state or not st.session_state["user_info"]:
        st.warning("로그인이 필요합니다.")
        return

    uid = st.session_state["user_info"]["user_id"]
    histories = db.get_user_interview_histories(uid)

    if not histories:
        st.info("ℹ️ 아직 저장된 과거 면접 이력이 존재하지 않습니다. 실전 면접방에서 첫 훈련을 완료해 보세요!")
        return

    # 레이아웃 구성
    col1, col2 = st.columns([1, 1.4], gap="large")

    with col1:
        st.markdown("##### 📅 면접 보관함 목록")
        options = []
        for h in histories:
            date_str = h["created_at"].strftime("%Y-%m-%d %H:%M")
            options.append(f"📌 [{date_str}] {h['company']} - {h['job']}")
            
        selected_option = st.radio("다시 읽어볼 면접 이력을 선택하세요", options, key="history_select_radio")
        
        selected_index = options.index(selected_option)
        selected_history = histories[selected_index]

        # [개선됨] 삭제 기능 구현
        st.markdown("---")
        with st.expander("🗑️ 면접 기록 삭제하기"):
            st.warning("삭제된 면접 기록은 복구할 수 없습니다.")
            confirm_delete = st.checkbox("선택한 기록을 영구 삭제하는 것에 동의합니다.")
            
            if st.button("🗑️ 선택한 면접 기록 삭제하기", key="delete_btn", type="primary", disabled=not confirm_delete):
                if db.delete_interview_history(selected_history["id"]):
                    st.success("✅ 삭제되었습니다.")
                    st.rerun() # 화면 새로고침하여 목록 갱신
                else:
                    st.error("❌ 삭제에 실패했습니다.")

    with col2:
        st.markdown(f"##### 📝 상세 보기: {selected_history['company']} - {selected_history['job']}")
        
        v_tab1, v_tab2 = st.tabs(["💬 대화 이력", "📊 AI 종합 리포트"])
        
        with v_tab1:
            try:
                chat_logs = json.loads(selected_history["chat_log"])
                for msg in chat_logs:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
            except:
                st.error("❌ 대화록 데이터를 복원하는 과정에서 오류가 발생했습니다.")
            
        with v_tab2:
            if selected_history.get("feedback_log"):
                try:
                    f_report = json.loads(selected_history["feedback_log"])
                    
                    sc1, sc2 = st.columns(2)
                    with sc1: 
                        st.metric(label="💯 당시 채점 점수", value=f"{f_report.get('total_score', 0)} / 100 점")
                    with sc2: 
                        st.metric(label="🏅 당시 합격 등급", value=f"[{f_report.get('grade', 'B')}] 등급")
                    st.markdown("---")
                    
                    with st.expander("✨ 당시 핵심 강점 (Strengths)", expanded=True):
                        st.success(f_report.get("strengths", "기록이 없습니다."))
                    with st.expander("⚠️ 당시 아쉬운 점 (Weaknesses)", expanded=True):
                        st.error(f_report.get("weaknesses", "기록이 없습니다."))
                    with st.expander("💡 면접관 제안 모범 답안 코칭", expanded=True):
                        st.info(f_report.get("best_answer_guide", "기록이 없습니다."))
                except:
                    st.error("❌ 피드백 데이터를 복원하는 과정에서 오류가 발생했습니다.")
            else:
                st.info("ℹ️ 해당 기록에 대한 피드백 데이터가 존재하지 않습니다.")