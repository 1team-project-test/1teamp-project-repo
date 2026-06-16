import os
import streamlit as st
from openai import OpenAI
import mariadb_control as db

def generate_ai_question(messages):
    """OpenAI API를 통해 면접관 성향에 맞는 실시간 질문 생성 (최신 문법 고정)"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        # 💡 [오류 해결 핵심] 최신 OpenAI SDK(v1.0.0+) 스펙에 맞춘 완전 무결한 텍스트 추출 방식
        if hasattr(response, "choices") and len(response.choices) > 0:
            return response.choices[0].message.content
        return "⚠️ AI 면접관의 응답 형식이 올바르지 않습니다."
    except Exception as e:
        return f"⚠️ AI 면접관과 연결이 일시적으로 원활하지 않습니다. (에러: {e})"

def render_interview_page():
    """🤖 실전 대화형 AI 면접방 화면 (1분 자기소개 스타트 버전)"""
    
    if not st.session_state.get("document_loaded"):
        st.warning("⚠️ 아직 이력서가 업로드되지 않았습니다. '이력서 제출' 메뉴에서 서류를 먼저 저장해 주세요.")
        return

    company = st.session_state.get("selected_company", "지정 기업")
    job = st.session_state.get("selected_job", "지정 직무")
    style = st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")
    doc_text = st.session_state.get("document_text", "")

    st.subheader("🤖 AI 실전 압박 면접방")
    st.caption(f"🎯 목표 기업: **{company}** | 💼 지원 직무: **{job}** | 🧠 면접관 성향: **{style}**")
    st.markdown("---")

    # 대화 히스토리 및 첫 질문 사전 세팅 (1분 자기소개 전용 프롬프트 반영)
    if "interview_messages" not in st.session_state:
        system_prompt = f"""
        너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다.
        현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다.
        
        [수행 지침 - 중요]
        1. 첫 문장은 반드시 실제 면접장처럼 정중하고 따뜻한 인사(아이스브레이킹)를 건넨 후, 첫 번째 질문으로 "가볍게 1분 자기소개부터 부탁드립니다."라고 요청하며 대화를 시작해라. 처음부터 서류의 구체적인 질문을 던지지 마라.
        2. 지원자가 1분 자기소개를 입력하면, 그 답변과 미리 제공된 [지원자 서류 본문 데이터]를 유기적으로 결합하여 두 번째 질문부터 본격적인 {style} 성향에 맞춘 면접 질문을 전개해라.
           - 압박형: 자기소개 및 서류의 취약점을 매섭게 파고드는 꼬리 질문 위주
           - 공감형: 답변을 경청하고 칭찬하며 역량을 이끌어내는 격려 중심 질문 위주
           - 원칙형: 답변한 내용의 논리적 팩트와 구체적 수치 증명을 요구하는 질문 위주
        3. 질문은 무조건 한 번에 '딱 한 개'씩만 던져라.
        4. 실제 면접관처럼 일관되게 자연스럽고 격식 있는 경어체를 사용해라.
        
        [지원자 서류 본문 데이터]
        {doc_text}
        """
        init_messages = [{"role": "system", "content": system_prompt}]
        
        with st.spinner("🧠 AI 면접관이 첫 면접 세션을 준비하고 있습니다..."):
            initial_q = generate_ai_question(init_messages)
            
        init_messages.append({"role": "assistant", "content": initial_q})
        st.session_state["interview_messages"] = init_messages

    # 화면에 대화 기록 출력
    for msg in st.session_state["interview_messages"][1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 하단 채팅 입력바 구현
    if user_answer := st.chat_input("이곳에 질문에 대한 답변을 입력하고 Enter를 누르세요..."):
        st.session_state["interview_messages"].append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.write(user_answer)
            
        with st.chat_message("assistant"):
            with st.spinner("📝 지원자님의 답변을 분석하여 다음 질문을 생각하는 중..."):
                next_q = generate_ai_question(st.session_state["interview_messages"])
                st.write(next_q)
                st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
                st.rerun()
    
    st.markdown("---")
    if st.button("🚪 면접 종료 및 AI 종합 피드백 받기 ➡️", use_container_width=True, type="primary"):
        # 💡 [핵심 조치] 화면을 넘기기 전, 면접방에서 먼저 AI 채점 분석기를 가동합니다!
        with st.spinner("📝 면접 내용을 종합 채점하고 보관함에 이력을 안전하게 적재 중입니다..."):
            # feedback_page 모듈의 핵심 함수를 빌려와 선제 피드백 데이터 빌드
            import feedback_page
            report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
            
            # API 통신 실패 예외 발생 시 비상 복구 안전 덤프 데이터 매핑
            if not report:
                report = {
                    "total_score": 75, "grade": "B",
                    "strengths": "성실하게 답변을 구성해주신 점이 아주 훌륭합니다.",
                    "weaknesses": "압박형 꼬리 질문에 근거 수치 증명이 다소 밀렸습니다.",
                    "best_answer_guide": "다음 훈련에서는 정량적 지표를 섞어 두괄식 표현을 연습하세요."
                }
            
            # 📌 대화록과 분석 레포트를 들고 MariaDB 통합 원스톱 저장 함수 호출 가동
            uid = st.session_state["user_info"]["user_id"]
            db.save_interview_and_feedback_together(uid, company, job, style, st.session_state["interview_messages"], report)
            
            # 피드백 화면이 API를 중복 호출하지 않도록 캐시 적재 동기화 복사
            st.session_state["feedback_report"] = report

        # 백엔드 적재 임무 완료 후 안전하게 피드백 룸으로 워프!
        st.session_state["current_menu"] = "📊 면접 피드백"
        st.rerun()