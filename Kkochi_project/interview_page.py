from local_llm import ask_local_question
import streamlit as st

def generate_ai_question(messages):
    try:
        system_content = ""
        last_user_answer = ""
        last_assistant_question = ""
        asked_questions = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]

            elif msg["role"] == "assistant":
                last_assistant_question = msg["content"]
                asked_questions.append(msg["content"])

            elif msg["role"] == "user":
                last_user_answer = msg["content"]

        prompt = f"""
{system_content}

[직전 면접관 질문]
{last_assistant_question}

[지원자의 최근 답변]
{last_user_answer}

[이미 질문한 내용]
{chr(10).join(asked_questions[1:][-5:])}

[추가 규칙]
직전 질문과 동일한 주제 또는 검증 포인트를 반복하지 않는다.
지원자의 최근 답변에서 가장 검증 가치가 높은 주장 1개만 선택한다.
지원자가 언급한 기술, 시스템, 프로젝트의 정의나 개념 설명을 요구하지 않는다.
반드시 역할, 행동, 판단 기준, 문제 해결 과정, 성과 중 하나를 검증한다.
설명 요청형 질문보다 의사결정 근거 검증 질문을 우선 생성한다.
기술명 자체보다 그 기술을 선택한 이유와 실제 활용 결과를 검증한다.
질문은 실제 행동, 판단 기준, 구현 결과 중 하나만 검증한다.
압박형 면접관은 칭찬하거나 평가하지 않는다.
질문 앞에 서론을 붙이지 않는다.
지원자의 답변을 다시 설명하게 만드는 질문은 금지한다.
답변 속 근거가 부족하거나 검증되지 않은 주장부터 검증한다.


[최종 출력 규칙]
면접관의 다음 꼬리질문 1개만 출력한다.
질문 외 설명을 출력하지 않는다.
반드시 한국어만 사용한다.
한자, 일본어, 중국어, 태국어 문자를 사용하지 않는다.
30자에서 80자 사이의 의문문으로 작성한다.

"""

        return ask_local_question(prompt)

    except Exception as e:
        return f"⚠️ Ollama 연결 오류: {e}"

def render_interview_page():
    """🤖 실전 대화형 AI 면접방 화면 (1분 자기소개 스타트 버전)"""
    
    if not st.session_state.get("document_loaded"):
        st.warning("⚠️ 아직 이력서가 업로드되지 않았습니다. '이력서 제출' 메뉴에서 서류를 먼저 저장해 주세요.")
        return

    company = st.session_state.get("selected_company", "지정 기업")
    job = st.session_state.get("selected_job", "지정 직무")
    style = st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")
    doc_text = st.session_state.get("document_text", "")[:2000]

    st.subheader("🤖 AI 실전 압박 면접방")
    st.caption(f"🎯 목표 기업: **{company}** | 💼 지원 직무: **{job}** | 🧠 면접관 성향: **{style}**")
    st.markdown("---")

    # 대화 히스토리 및 첫 질문 사전 세팅 (1분 자기소개 전용 프롬프트 반영)
    if "interview_messages" not in st.session_state:
        system_prompt = f"""
너는 {company}의 {job} 채용을 담당하는 실제 면접관이다.
지원자의 이력서 및 자기소개서와 면접 답변을 바탕으로 1:1 면접을 진행한다.

[면접관 역할]
- 프로젝트 발표 심사위원이 아니라 실제 채용 면접관으로 질문한다.
- 지원자의 역할, 행동, 판단 기준, 문제 해결 과정, 결과를 검증한다.
- {style} 성향에 맞춰 질문한다.

[질문 기준]
- 질문은 한 번에 1개만 한다.
- 지원자 답변에서 가장 검증 가치가 높은 주장 1개만 선택한다.
- 기술 설명보다 기술 선택 이유, 판단 기준, 실제 행동, 결과를 우선 검증한다.
- 같은 주제나 같은 검증 포인트를 반복하지 않는다.
- 칭찬이나 평가 없이 바로 질문한다.
- 프로젝트나 기술의 정의를 묻는 질문은 금지한다.
- "무엇인가요", "설명해주세요", "소개해주세요" 형태의 질문은 금지한다.
- 기술 설명보다 실제 문제 해결 과정과 의사결정 근거를 우선 검증한다.
- 지원자가 수행한 행동과 결과를 검증하는 질문을 우선 생성한다.
- 성과를 언급한 경우 측정 기준이나 수치를 검증한다.
- 팀 프로젝트를 언급한 경우 본인의 기여도를 검증한다.
- 기술을 언급한 경우 선택 이유 또는 사용 중 발생한 문제를 검증한다.
- 답변의 취약점이나 근거가 부족한 부분을 우선 질문한다.

[금지]
- 자기소개를 다시 요청하지 않는다.
- 지원자의 답변을 복사하거나 요약하지 않는다.
- 질문 외 설명을 출력하지 않는다.
- 한자, 일본어, 중국어, 태국어 문자를 사용하지 않는다.
- 제공되지 않은 개인정보를 만들지 않는다.

[지원자 서류 본문 데이터]
{doc_text}
"""
        init_messages = [{"role": "system", "content": system_prompt}]
        
        initial_q = """
        안녕하세요. 면접에 참여해 주셔서 감사합니다.
        가볍게 1분 자기소개부터 부탁드립니다.
        """
            
        init_messages.append({"role": "assistant", "content": initial_q})
        st.session_state["interview_messages"] = init_messages

    # 화면에 대화 기록 출력
    for msg in st.session_state["interview_messages"]:
        if msg["role"] == "system":
            continue

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
    # interview_page.py 맨 마지막 라인 바로 아래에 붙여넣어 주세요!
    st.markdown("---")
    if st.button("🚪 면접 종료하고 AI 종합 피드백 받기 ➡️", use_container_width=True, type="primary"):
        st.session_state["current_menu"] = "📊 면접 피드백"
        st.rerun()