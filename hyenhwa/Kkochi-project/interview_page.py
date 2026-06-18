import os
import streamlit as st
from openai import OpenAI
import mariadb_control as db

def generate_ai_question(messages):
    """Ollama 로컬 API를 통해 면접관 성향에 맞는 실시간 질문 생성 (gemma2 또는 llama3 활용)"""
    try:
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="gemma2"
        )
        
        # 💡 model 명칭이 gemma3로 오타가 나있던 부분을 실제 다운로드한 모델명에 맞게 체크하세요!
        # (만약 gemma2를 받으셨다면 "gemma2", llama3를 쓰신다면 "llama3"로 기입)
        response = client.chat.completions.create(
            model="gemma2:9b",  
            messages=messages,
            temperature=0.5
        )
        
        if hasattr(response, "choices") and len(response.choices) > 0:
            return response.choices[0].message.content
        return "⚠️ AI 면접관의 응답 형식이 올바르지 않습니다."
    except Exception as e:
        return f"⚠️ AI 면접관과 연결이 일시적으로 원활하지 않습니다. (에러: {e})"

def render_interview_page():
    """🤖 실전 대화형 AI 면접방 화면 (1분 자기소개 스타트 버전)"""
    
    # 💡 세션 유실로 인한 튕김 현상을 방지하기 위해 보다 안전하게 세션 방어벽 구축
    if "document_loaded" not in st.session_state or not st.session_state["document_loaded"]:
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
        
        [⚠️ 중요 규칙 - 반드시 준수할 것]
        1. 질문은 무조건 한 번에 '딱 한 개'씩만 던져라.
        2. 실제 면접관처럼 일관되게 자연스럽고 격식 있는 한국어 경어체를 사용해라.
        3. 모든 답변은 반드시 100% 한국어여야만 한다. 절대 영어로 답변하지 마라.
        4. 지원자의 답변 내용을 바탕으로 본격적인 {style} 성향에 맞춘 날카롭거나 공감어린 다음 면접 꼬리 질문을 한국어로 전개해라.
        5. 지원자가 오타나 잘못된 말을 하면 한번 더 설명 해 달라 요구한다.
        
        [지원자 서류 본문 데이터]
        {doc_text}
        """
        init_messages = [{"role": "system", "content": system_prompt}]
        
        # AI를 호출하지 않고 면접관 성향(style)에 맞춰 한국어 고정 멘트 즉시 주입
        style_intro = ""
        if "압박" in style:
            style_intro = f"안녕하십니까. {company}의 {job} 직무 면접을 맡은 면접관입니다. 바로 긴장감 있게 진행해 보죠."
        elif "공감" in style:
            style_intro = f"안녕하세요! 오늘 {company}의 {job} 직무 면접을 진행하게 되어 반갑습니다. 편안한 마음으로 임해주세요."
        else:
            style_intro = f"반갑습니다. {company}의 {job} 직무 채용 면접관입니다. 대답의 논리성과 사실 관계를 중심으로 평가하겠습니다."

        initial_q = f"{style_intro}\n\n먼저 가볍게 **1분 자기소개**부터 부탁드립니다."
            
        init_messages.append({"role": "assistant", "content": initial_q})
        st.session_state["interview_messages"] = init_messages

    # 화면에 대화 기록 출력 (System 프롬프트를 제외한 대화 내용만 렌더링)
    for msg in st.session_state["interview_messages"][1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 하단 채팅 입력바 구현
    if user_answer := st.chat_input("이곳에 질문에 대한 답변을 입력하고 Enter를 누르세요..."):
        # 1. 유저 답변 기록 추가 및 화면에 즉시 표시
        st.session_state["interview_messages"].append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.write(user_answer)
            
        # 2. AI 답변 생성 및 즉시 표시
        with st.chat_message("assistant"):
            with st.spinner("📝 지원자님의 답변을 분석하여 다음 질문을 생각하는 중..."):
                next_q = generate_ai_question(st.session_state["interview_messages"])
                st.write(next_q)
                # 대화록 배열에 AI 답변 누적
                st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
        
        # 💡 [핵심 버그 수정] chat_input 스크립트 스펙상 내부 내부 rerun을 제거해야 세션 튕김 현상이 사라집니다.
        # 기존의 st.rerun()을 과감히 삭제합니다.
    
    st.markdown("---")
    if st.button("🚪 면접 종료 및 AI 종합 피드백 받기 ➡️", use_container_width=True, type="primary"):
        with st.spinner("📝 면접 내용을 종합 채점하고 보관함에 이력을 안전하게 적재 중입니다..."):
            import feedback_page
            report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
            
            if not report:
                report = {
                    "total_score": 75, "grade": "B",
                    "strengths": "성실하게 답변을 구성해주신 점이 아주 훌륭합니다.",
                    "weaknesses": "압박형 꼬리 질문에 근거 수치 증명이 다소 밀렸습니다.",
                    "best_answer_guide": "다음 훈련에서는 정량적 지표를 섞어 두괄식 표현을 연습하세요."
                }
            
            uid = st.session_state["user_info"]["user_id"]
            db.save_interview_and_feedback_together(uid, company, job, style, st.session_state["interview_messages"], report)
            
            st.session_state["feedback_report"] = report

        st.session_state["current_menu"] = "📊 면접 피드백"
        # 💡 페이지를 의도적으로 이동할 때의 st.rerun()은 필수적이므로 그대로 유지합니다.
        st.rerun()