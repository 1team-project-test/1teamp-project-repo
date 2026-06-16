import os
import json
import streamlit as st
from openai import OpenAI
import mariadb_control as db

def generate_interview_feedback(history_messages):
    """OpenAI API를 활용해 전체 면접 대화 이력을 정밀 분석하여 종합 평가 리포트 생성 (최신 문법 반영)"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 복잡한 메시지 딕셔너리 구조를 순수 텍스트 대화록으로 문자열 변환
        conversation_log = ""
        for msg in history_messages:
            if msg["role"] == "assistant":
                conversation_log += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_log += "지원자: {}\n".format(msg["content"])
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "너는 인사담당자이자 채용 전문가이다. 제공된 면접관과 지원자의 1:1 대화 기록을 분석해서 반드시 다음 5개의 키를 가진 JSON 오브젝트로만 응답해라: 'total_score' (100점 만점 기준 정수 점수), 'grade' (S, A, B, C 중 하나의 등급 문자), 'strengths' (핵심 강점 요약), 'weaknesses' (아쉬웠던 논리적 약점 또는 보완점), 'best_answer_guide' (향후 면접을 위한 모범 답안 가이드 코칭). 모든 값은 한글 경어체 문장으로 정성스럽게 작성해라."},
                {"role": "user", "content": "이하 면접 대화 기록을 평가해라:\n{}".format(conversation_log)}
            ],
            temperature=0.3
        )
        
        # 💡 [오류 해결 핵심] 최신 OpenAI SDK 스펙에 맞춰 안전하게 텍스트 추출 가동
        if hasattr(response, "choices") and len(response.choices) > 0:
            return json.loads(response.choices[0].message.content) # choices 리스트의 0번째 인덱스를 명시하여 에러 해결
        return None
    except Exception as e:
        print("[OpenAI Feedback Error] 상세 원인: {}".format(e))
        return None

def render_feedback_page():
    """📊 AI 면접 종합 피드백 & 채점 리포트 화면 (중복 호출 차단 보정판)"""
    st.subheader("📊 AI 면접 채점 및 종합 피드백 리포트")
    st.caption("진행하신 실전 압박 면접 대화 이력을 바탕으로 AI 채용 전문가가 도출한 역량 평가서입니다.")
    st.markdown("---")

    # 예외 방어: 가동 기록이 없으면 돌려보내기
    if "interview_messages" not in st.session_state or len(st.session_state["interview_messages"]) <= 2:
        st.warning("⚠️ 면접 대화 기록이 존재하지 않습니다. 실전 면접방에서 먼저 면접을 진행해 주세요.")
        if st.button("🤖 면접방으로 돌아가기"):
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
        return

    # 💡 면접방에서 이미 연산 및 저장을 끝내고 준 데이터를 안전하게 수령 (중복 호출 및 미보관 버그 완전 파괴)
    if "feedback_report" not in st.session_state:
        st.info("ℹ️ 현재 실시간 면접 종료 세션이 아닙니다. 과거 기록은 '면접 이력 관리' 메뉴를 통해 안전하게 상시 열람하실 수 있습니다.")
        return

    report = st.session_state["feedback_report"]
    # (이하 기존 스코어 보드 및 아코디언 출력 소스 코드 부분은 수정 없이 그대로 유지)

    # 3. 최상단 스코어 보드 레이아웃 시각화
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="💯 종합 채점 점수", value="{} / 100 점".format(report.get("total_score", 0)))
    with col2:
        st.metric(label="🏅 예상 합격 등급", value="[{}] 등급".format(report.get("grade", "B")))

    st.markdown("---")

    # 4. 아코디언 스타일 상세 항목 가시화
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