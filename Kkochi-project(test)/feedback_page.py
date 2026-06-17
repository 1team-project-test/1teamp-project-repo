import os
import json
import streamlit as st
import requests

def generate_interview_feedback(history_messages):
    """🤖 [온프레미스] gemma2:9b 모델을 활용한 고해상도 상세 면접 채점 보고서 생성"""
    try:
        url = "http://localhost:11434/api/generate"
        
        conversation_log = ""
        for msg in history_messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            if msg["role"] == "assistant":
                conversation_log += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_log += "지원자: {}\n".format(msg["content"])

        # 💡 [프롬프트 가이드라인 대폭 강화] 단답형 출력을 금지하고 항목별 3~4줄 이상의 구체적 실전 분석 강제
        final_prompt = f"""
        너는 대기업 인사팀장 출신의 베테랑 채용 전문가이자 professional 면접 코치이다. 
        제공된 면접 대화 기록을 면밀히 스캔하여 지원자의 역량을 날카롭고 세부적으로 채점하십시오.
        반드시 다음 5개의 키를 가진 JSON 오브젝트로만 응답하고, 마크다운 기호 없이 순수 JSON만 반환해라.

        [JSON 반환 스키마 및 가이드라인 - 중요]
        1. 'total_score' : 100점 만점 기준의 정수 점수.
        2. 'grade' : S, A, B, C 중 하나의 등급 문자.
        3. 'strengths' : 지원자의 답변 속에서 돋보인 논리성, 직무 전문성, 태도적 강점을 구체적인 답변 사례를 인용하여 '최소 3문장(4줄) 이상' 상세히 칭찬하십시오. 단답형이나 한 줄 평가는 절대 금지합니다.
        4. 'weaknesses' : 면접관의 압박/꼬리 질문에 답변할 때 부족했던 부분, 논리적 모순, 혹은 정량적 성과(지표) 표현의 아쉬움을 날카롭게 짚어내고 '최소 3문장(4줄) 이상' 구체적으로 지적하십시오.
        5. 'best_answer_guide' : 향후 이 기업/직무 면접에서 무조건 합격하기 위해 답변을 어떻게 리프레이밍해야 하는지 두괄식(STAR 기법) 작성 요령을 포함하여 '최소 4문장(5줄) 이상'의 구체적인 솔루션과 모범 답변 예시 가이드를 친절한 경어체로 작성하십시오.

        [평가 대상 면접 대화록 기록]
        {conversation_log}
        """

        payload = {
            "model": "gemma2:9b",
            "prompt": final_prompt.strip(),
            "options": {
                "temperature": 0.4,       # 평가의 객관성을 위해 정확도를 높임
                "num_ctx": 8192,          # 🧠 장문의 리포트 작성이 가능하도록 단기 뇌 용량 8K 최대 확보
                "repeat_penalty": 1.2
            },
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=90) # 상세 연산을 위해 타임아웃을 90초로 연장
        
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json:
                res_content = res_json["response"].strip()
                return json.loads(res_content)
        return None
    except Exception as e:
        print("[Local AI Feedback Error] 상세 원인: {}".format(e))
        return None

def render_feedback_page():
    """📊 AI 면접 종합 피드백 & 채점 리포트 화면"""
    st.subheader("📊 AI 면접 채점 및 종합 피드백 리포트")
    st.caption("진행하신 실전 압박 면접 대화 이력을 바탕으로 AI 채용 전문가가 도출한 역량 평가서입니다.")
    st.markdown("---")

    if "interview_messages" not in st.session_state or len(st.session_state["interview_messages"]) <= 2:
        st.warning("⚠️ 면접 대화 기록이 존재하지 않습니다. 실전 면접방에서 먼저 면접을 진행해 주세요.")
        if st.button("🤖 면접방으로 돌아가기"):
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
        return

    if "feedback_report" not in st.session_state:
        st.info("ℹ️ 현재 실시간 면접 종료 세션이 아닙니다. 과거 기록은 '면접 이력 관리' 메뉴를 통해 안전하게 상시 열람하실 수 있습니다.")
        return

    report = st.session_state["feedback_report"]

    col1, col2 = st.columns(2)
    with col1: st.metric(label="💯 종합 채점 점수", value="{} / 100 점".format(report.get("total_score", 0)))
    with col2: st.metric(label="🏅 예상 합격 등급", value="[{}] 등급".format(report.get("grade", "B")))
    st.markdown("---")

    # 💡 상세해진 텍스트 가시성을 위해 내부 여백 디자인 레이아웃 유지
    with st.expander("✨ 지원자님의 핵심 강점 (Strengths)", expanded=True):
        st.success(report.get("strengths", "분석된 내용이 없습니다."))
    with st.expander("⚠️ 아쉬운 점 및 취약점 (Weaknesses)", expanded=True):
        st.error(report.get("weaknesses", "분석된 내용이 없습니다."))
    with st.expander("💡 면접관이 제안하는 핵심 모범 답안 가이드 (Coaching)", expanded=True):
        st.info(report.get("best_answer_guide", "분석된 내용이 없습니다."))

    st.markdown("---")
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