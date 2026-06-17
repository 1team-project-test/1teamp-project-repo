from local_llm import ask_local_ai
import streamlit as st

def generate_ai_question(messages):
    try:
        system_content = ""
        last_user_answer = ""

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                last_user_answer = msg["content"]

        prompt = f"""
{system_content}

[지원자의 최근 답변]
{last_user_answer}

[최종 출력 규칙]
지원자의 마지막 답변만 분석한다.
첫 질문은 이미 완료되었다.
이제부터는 지원자의 마지막 답변을 바탕으로 후속 꼬리질문만 생성한다.
대화 내용을 반복하지 않는다.
지원자의 답변을 복사하지 않는다.
지원자의 답변을 요약하지 않는다.
지원자의 마지막 문장을 그대로 인용하지 않는다.
자기소개를 다시 요청하지 않는다.
면접관의 다음 꼬리질문 1개만 출력한다.
반드시 한국어만 사용한다.
한자, 일본어, 중국어, 태국어 문자를 절대 사용하지 않는다.
영어 단어를 불필요하게 섞지 않는다.
질문 앞에 [AI면접관], [지원자], [시스템] 같은 라벨을 붙이지 않는다.
질문 외 설명을 출력하지 않는다.
반드시 새로운 의문문으로 시작한다.

"""

        return ask_local_ai(prompt)

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
    doc_text = st.session_state.get("document_text", "")[:1200]

    st.subheader("🤖 AI 실전 압박 면접방")
    st.caption(f"🎯 목표 기업: **{company}** | 💼 지원 직무: **{job}** | 🧠 면접관 성향: **{style}**")
    st.markdown("---")

    # 대화 히스토리 및 첫 질문 사전 세팅 (1분 자기소개 전용 프롬프트 반영)
    if "interview_messages" not in st.session_state:
        system_prompt = f"""
        너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다.
        현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다.
        
        [수행 지침 - 중요]
        1. 첫 자기소개 답변 이후부터 서류와 답변을 바탕으로 질문을 생성해라.
        2. 지원자가 1분 자기소개를 입력하면, 그 답변과 미리 제공된 [지원자 서류 본문 데이터]를 유기적으로 결합하여 두 번째 질문부터 본격적인 {style} 성향에 맞춘 면접 질문을 전개해라.
           - 압박형: 자기소개 및 서류의 취약점을 매섭게 파고드는 꼬리 질문 위주
           - 공감형: 답변을 경청하고 칭찬하며 역량을 이끌어내는 격려 중심 질문 위주
           - 원칙형: 답변한 내용의 논리적 팩트와 구체적 수치 증명을 요구하는 질문 위주
        3. 질문은 무조건 한 번에 '딱 한 개'씩만 던져라.
        4. 실제 면접관처럼 일관되게 자연스럽고 격식 있는 경어체를 사용해라.
        5. 반드시 한국어만 사용한다.
        6. 영어단어를 불필요하게 섞지않는다.
        7. 한자, 일본어, 중국어, 태국어 문자를 절대 사용하지 않는다.
        8. 지원자의 이름을 추측하거나 생성하지 않는다.
        9. 제공되지 않은 개인정보를 만들어내지 않는다.
        10. "face", "[Your Name]", "today" 와 같은 표현을 사용하지 않는다.
        11. AI 개발, 코칭 관심사 등 지원자가 언급하지 않은 내용을 만들어내지 않는다.
        12. 대화 내용을 반복하지 않는다.
        13. 지원자의 답변을 복사하지 않는다.
        14. 자기소개를 다시 요청하지 않는다.
        15. 면접관의 다음 질문 1개만 출력한다.
        16. 질문 앞에 [AI면접관], [지원자], [시스템] 같은 라벨을 붙이지 않는다.
        
        [검증 원칙]
        18. 지원자 답변에서 가장 검증 가치가 높은 핵심 주장 1개를 선택한다.
        19. 추상적 표현(개선했다, 향상되었다, 최적화했다, 해결했다, 경험했다, 기여했다, 성공했다 등)이 포함된 경우 반드시 구체적인 근거를 요구한다.
        20. 성과나 결과를 언급한 경우 정량적 수치 또는 측정 방법을 검증한다.
        21. 경험을 언급한 경우 실제 수행 과정과 행동을 검증한다.
        22. 프로젝트 또는 업무 경험을 언급한 경우 본인의 역할과 기여도를 검증한다.
        23. 팀 활동을 언급한 경우 본인이 직접 수행한 업무와 다른 구성원의 업무를 구분하도록 검증한다.
        24. 기술, 도구, 방법론, 시스템 등을 언급한 경우 선택 이유와 실제 활용 방식을 검증한다.
        25. 문제 해결 경험을 언급한 경우 문제의 원인, 해결 과정, 판단 기준을 검증한다.
        26. 결과만 설명하고 과정이 없는 경우 과정 중심의 설명을 유도한다.
        27. 답변의 진실성, 전문성, 문제 해결 능력을 동시에 검증할 수 있는 질문을 우선 생성한다.
        
        [질문 생성 기준]
        28. 예 또는 아니오로 답변할 수 있는 질문은 생성하지 않는다.
        29. "왜", "어떻게", "무엇을 기준으로", "구체적으로", "실제로" 등의 표현을 적극 활용한다.
        30. 지원자가 가장 깊이 있는 경험과 사고 과정을 설명할 수 있는 질문을 우선 생성한다.
        31. 답변 내용보다 한 단계 더 깊은 수준의 사고를 요구하는 질문을 생성한다.
        32. 단순 사실 확인보다 경험, 판단, 행동, 결과를 설명할 수 있는 질문을 생성한다.
        33. 현재 답변과 직전 대화 흐름을 고려하여 가장 적절한 다음 질문을 생성한다.
        34. 지원자의 마지막 문장을 그대로 인용하지 않는다.
        35. 지원자의 답변을 요약한 뒤 질문하지 않는다.
        36. 질문 외의 설명문을 출력하지 않는다.
        37. 반드시 새로운 질문 문장으로 시작한다.
        38. 질문 첫 문장은 의문문이어야 한다.
        39. 지원자의 답변 일부를 복사하여 질문 앞에 붙이지 않는다.
        40. 한 번의 질문에서는 하나의 핵심 주장만 검증한다.
        41. 하나의 질문 안에 두 개 이상의 독립적인 질문을 포함하지 않는다.
        42. "무엇이며, 어떻게, 왜" 와 같이 여러 질문을 나열하지 않는다.
        43. 가장 검증 가치가 높은 주제 하나만 선택하여 질문한다.
        44. 질문은 30자~80자 내외로 간결하게 작성한다.
        45. 불필요한 배경 설명 없이 핵심 검증 질문부터 시작한다.
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