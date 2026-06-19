import os
import json
import streamlit as st
import requests
import re # 마크다운을 뜯어내기 위한 정규식 라이브러리

def generate_interview_feedback(history_messages):
    """🤖 [온프레미스] gemma2:9b 모델을 활용한 고해상도 상세 면접 채점 보고서 생성 (JSON 파싱 강화)"""
    try:
        url = "http://localhost:11434/api/generate"
        
        conversation_log = ""
        for msg in history_messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            if msg["role"] == "assistant":
                conversation_log += f"면접관: {msg['content']}\n"
            elif msg["role"] == "user":
                conversation_log += f"지원자: {msg['content']}\n"

        final_prompt = f"""
        너는 대기업 인사팀장 출신의 베테랑 채용 전문가이자 professional 면접 코치이다. 
        제공된 면접 대화 기록을 면밀히 스캔하여 지원자의 역량을 채점해라.
        
        [절대 지침]
        1. 반드시 아래의 [JSON 응답 템플릿] 양식에 맞추어 순수한 JSON 객체 하나만 출력해라.
        2. 마크다운 기호(```json 등)는 절대 사용하지 마라.
        3. 문장 안에서 줄바꿈이 필요하면 실제 엔터를 치지 말고 반드시 '\\n' 기호를 써라.
        4. 문장 안에서 강조를 하고 싶다면 쌍따옴표(") 대신 홑따옴표(')를 써라.

        [JSON 응답 템플릿]
        {{
            "total_score": 85,
            "grade": "A",
            "strengths": "지원자의 답변 속에서 돋보인 논리성, 직무 전문성 등을 구체적인 답변 사례를 인용하여 최소 3문장 이상 상세히 칭찬해라.",
            "weaknesses": "답변할 때 부족했던 부분, 논리적 모순 등을 최소 3문장 이상 날카롭게 지적해라.",
            "best_answer_guide": "**STAR 기법 활용 예시:**\\n\\n- **Situation**: (구체적인 상황 제시)\\n- **Task**: (해결해야 했던 과제)\\n- **Action**: (본인의 구체적인 행동과 노력)\\n- **Result**: (창출한 성과 및 배운 점)\\n\\n(위 양식처럼 반드시 '\\n' 기호와 불릿('-')을 사용하여 가독성 좋은 마크다운 리스트 형태로 모범 답안을 제안해라.)"
        }}

        [평가 대상 면접 대화록 기록]
        {conversation_log}
        """

        payload = {
            "model": "gemma2:9b",
            "prompt": final_prompt.strip(),
            "options": {
                "temperature": 0.3,       # 💡 창의성보다는 양식 준수(정확도)를 위해 온도를 낮춤
                "num_ctx": 8192,
                "repeat_penalty": 1.2
            },
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json:
                res_content = res_json["response"].strip()
                
                # # 💡 [디버깅] 터미널에 원본 텍스트 적나라하게 출력하기!
                # print("\n🚨 [디버깅] AI가 뱉어낸 진짜 원본 텍스트:")
                # print(res_content)
                # print("=========================================\n")
                
                # 💡 [궁극의 파싱 방어] 텍스트 전체에서 무조건 '{' 부터 '}' 까지만 칼같이 도려내기
                match = re.search(r'\{[\s\S]*\}', res_content)
                if match:
                    clean_json_str = match.group(0)
                    
                    # strict=False 옵션: AI가 문자열 중간에 무식하게 진짜 엔터를 쳤더라도 에러 없이 융통성 있게 넘어갑니다.
                    return json.loads(clean_json_str, strict=False)
                else:
                    print("[Local AI Feedback Error] 텍스트에서 JSON 괄호 '{ }' 를 찾을 수 없습니다.")
                    return None
                
        return None
    except Exception as e:
        print(f"[Local AI Feedback Error] 상세 원인: {e}")
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
    with col1: st.metric(label="💯 종합 채점 점수", value=f"{report.get('total_score', 0)} / 100 점")
    with col2: st.metric(label="🏅 예상 합격 등급", value=f"[{report.get('grade', 'B')}] 등급")
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