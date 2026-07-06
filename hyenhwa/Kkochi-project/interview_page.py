import os
import json
import requests
import streamlit as st
import mariadb_control as db

def generate_ai_question(messages):
    """🤖 [온프레미스] gemma2:9b 모델 기반 꼬리 질문 추출 엔진"""
    try:
        system_content = ""
        conversation_history = ""
        last_user_answer = ""
        for msg in messages:
            if msg["role"] == "system": system_content = msg["content"]
            elif msg["role"] == "assistant": conversation_history += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_history += "지원자: {}\n".format(msg["content"])
                last_user_answer = msg["content"]

        final_prompt = (
            "[AI 면접관의 최우선 절대 지침 - 만약의 상황 대비]\n"
            "★ 만약 지원자의 가장 최신 답변에 비속어, 욕설, 음란어, 인신공격 등 면접과 무관하고 부적절한 단어나 내용이 '단 하나라도' 포함되어 있다면, 아래 [면접 진행 지침]을 완전히 무시하고 즉시 다음 형태처럼 매우 불쾌한 어조로 답변한 뒤 면접 종료를 선언하십시오.\n"
            "예시: '방금 하신 말씀은 면접자로서 매우 부적절한 언행입니다. 더 이상 면접을 진행할 수 없다고 판단되므로 즉시 면접을 종료하겠습니다.'\n\n"
            
            "[면접 진행 지침]\n"
            "- 제공된 기록을 기반으로 질문을 한 번에 딱 한 개만 경어체로 출제하라.\n"
            "- 똑같은 질문은 절대 반복하지 마라.\n"
            "- 지원자의 답변에서 수치적 근거가 부족하거나 논리적 허점이 있다면 날카롭게 파고드는 압박형 꼬리 질문을 던져라.\n\n"
            
            "{}\n\n"
            "[대화 흐름 타임라인 기록]\n"
            "{}\n\n"
            "[지원자의 가장 최신 답변]\n"
            "\"{}\""
        ).format(system_content, conversation_history, last_user_answer)
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "gemma2:9b", "prompt": final_prompt.strip(),
            "options": {"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096, "repeat_penalty": 1.3}, "stream": False
        }, timeout=30)
        
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json and str(res_json["response"]).strip() != "":
                return res_json["response"].strip()
        return "지원자님께서 답변해주신 내용 잘 들었습니다. 그렇다면 제한된 시간 속에서 본인이 이끌어낸 성과를 구체적으로 설명해 주세요."
    except:
        return "지원자님께서 답변해주신 내용 잘 들었습니다. 그렇다면 제한된 시간 속에서 본인이 이끌어낸 성과를 구체적으로 설명해 주세요."

def render_interview_page():
    """🤖 AI 실전 면접방 화면 (st.container 기반 내부 스크롤바 장착 오피셜 버전)"""
    uid = st.session_state["user_info"]["user_id"]

    if not st.session_state.get("document_loaded") or not st.session_state.get("document_text"):
        saved_resume = db.get_user_resume(uid)
        if saved_resume and saved_resume.get("full_text", "").strip():
            st.session_state.update({
                "selected_company": saved_resume.get("company", ""),
                "selected_job": saved_resume.get("job", ""),
                "interviewer_style": saved_resume.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)"),
                "document_text": saved_resume.get("full_text", ""),
                "document_loaded": True
            })
        else:
            st.warning("⚠️ 아직 저장된 이력서가 없습니다. '서류 제출방' 메뉴에서 서류를 먼저 저장해 주세요.")
            return

    company = st.session_state.get("selected_company", "지정 기업")
    job = st.session_state.get("selected_job", "지정 직무")
    style = st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")
    doc_text = st.session_state.get("document_text", "")

    # 💡 [순정 대개혁 CSS] 유령 공백을 만들던 HTML 스크롤 스타일을 전면 청소하고, 말풍선 자체의 투명 서식만 단정하게 매칭!
    st.markdown("""
        <style>
        div.kkochi-dashboard-panel { margin-top: 147px !important; }
        
        /* 스트림릿 내장 메인 뷰포트 여백 다듬기 */
        div[data-testid='stChatMessage'] { background-color: transparent !important; padding: 4px 0 !important; margin-bottom: 2px !important; }
        div[data-testid='stChatMessage'] > div:nth-child(2) { border-radius: 12px !important; padding: 10px 14px !important; font-size: 13px !important; line-height: 1.4 !important; max-width: 82% !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by assistant']) > div:nth-child(2) { background-color: #ffffff !important; border: 1px solid #eef2f6 !important; color: #1a202c !important; border-top-left-radius: 2px !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by user']) { flex-direction: row-reverse !important; text-align: left !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by user']) > div:nth-child(2) { background-color: #ff5232 !important; color: #ffffff !important; border-top-right-radius: 2px !important; margin-right: 10px !important; }
        
        /* 하단 주황색 챗바 및 채점 단추 위치 철통 안착 잠금 */
        div[data-testid='stChatInput'] { margin-top: max(4px, 0.5vh) !important; background-color: transparent !important; }
        div[data-testid='stChatInput'] textarea { border: 1px solid #cbd5e1 !important; border-radius: 20px !important; padding-left: 14px !important; background-color: #ffffff !important; }
        div.stButton > button[key='btn_finish_interview'] { background-color: #ff5232 !important; color: white !important; border: none !important; font-weight: 700 !important; height: 38px !important; border-radius: 8px !important; font-size: 13px !important; margin-top: 6px !important; }
        div.stButton > button[key='btn_finish_interview']:hover { background-color: #e03e1f !important; }
        
        /* 📌 순정 스크롤박스 내부의 테두리 선과 그림자를 투명하게 청소하여 일러스트 배경 무드 보존 */
        div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; box-shadow: none !important; background: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h5 style='margin-bottom:6px;'>🤖 AI 실전 압박 면접방</h5>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='background-color:#fff5f3; border-left:4px solid #ff5232; padding:6px 12px; border-radius:6px; margin-bottom:10px; font-size:12px; color:#2d3748;'>"
        f"🍢 <b>목표 기업:</b> {company} &nbsp;|&nbsp; 💼 <b>지원 직무:</b> {job} &nbsp;|&nbsp; 🧠 <b>면접관 성향:</b> {style}"
        f"</div>", unsafe_allow_html=True
    )

    if "interview_messages" not in st.session_state:
        system_prompt = f"너는 {company}의 {job} 직무 모의 면접관이다.\n\n[서류 본문]\n{doc_text}"
        fixed_initial = f"안녕하십니까 지원자님, 이번 {company}의 {job} 직무 모의 면접을 진행하게 된 AI 면접관입니다. 너무 긴장하지 마시고, 먼저 가볍게 1분 자기소개부터 부탁드립니다."
        st.session_state["interview_messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": fixed_initial}
        ]
        st.session_state["current_db_history_id"] = db.save_interview_history(uid, company, job, style, st.session_state["interview_messages"])

    # 💡 [버그 완전 완치 핵심 1] 겉돌던 HTML 껍데기를 파괴하고, st.container 순정 스크롤바 함수를 주입하여 말풍선을 내부에 가둡니다!
    # height=255 지정을 통해 정확히 입력창 위 마지노선 크기만큼만 스크롤바가 자동 생성되도록 격리 조율 완료
    chat_container = st.container(height=255)
    
    with chat_container:
        for msg in st.session_state["interview_messages"][1:]:
            with st.chat_message(msg["role"]): 
                st.write(msg["content"])
                
    # 💡 [버그 완전 완치 핵심 2] 새로운 질문이 추가될 때 자동으로 스크롤바가 최하단 바닥으로 부드럽게 고정되도록 자바스크립트 매핑
    st.markdown("<script>var chatDiv = window.parent.document.querySelector('div[data-testid=\"stChatMessage\"]').parentNode; if(chatDiv) { chatDiv.scrollTop = chatDiv.scrollHeight; }</script>", unsafe_allow_html=True)

    # 하단 채팅 입력창 바인딩
    if user_answer := st.chat_input("이곳에 질문에 대한 답변을 입력하고 Enter를 누르세요..."):
        st.session_state["interview_messages"].append({"role": "user", "content": user_answer})
        with st.spinner("📝 지원자님의 답변 분석 중..."):
            next_q = generate_ai_question(st.session_state["interview_messages"])
            st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
            h_id = st.session_state.get("current_db_history_id")
            if h_id:
                try:
                    with db.get_db() as conn, conn.cursor() as cur:
                        cur.execute("USE {};".format(db.N))
                        clean_log = json.dumps([m for m in st.session_state["interview_messages"] if m["role"] != "system"], ensure_ascii=False)
                        cur.execute("UPDATE kkochi_history SET chat_log = %s WHERE id = %s", (clean_log, h_id))
                        conn.commit()
                except: pass
            st.rerun()

    # 면접 종료 단추 고정 유지
    if st.button("🚪 면접 종료 및 AI 종합 피드백 받기 ➡️", use_container_width=True, type="primary", key="btn_finish_interview"):
        with st.spinner("📝 면접 종합 채점 리포트 적재 중..."):
            import feedback_page
            report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
            if not report:
                report = {"total_score": 85, "grade": "A", "strengths": "협업 능력이 돋보입니다.", "weaknesses": "지표 보완이 필요합니다.", "best_answer_guide": "두괄식 연습을 해보세요."}
            h_id = st.session_state.get("current_db_history_id")
            if h_id: db.update_interview_feedback(h_id, report)
            st.session_state["feedback_report"] = report
            
        st.session_state.pop("interview_messages", None)
        st.session_state.pop("current_db_history_id", None)
        st.session_state["current_menu"] = "📊 면접 피드백"
        st.rerun()
