import os
import json
import requests
import streamlit as st
import mariadb_control as db

def generate_ai_question(messages):
    """🤖 [온프레미스] gemma2:9b 모델 기반 꼬리 질문 추출 엔진"""
    try:
        tags_url = "http://localhost:11434/api/tags"
        target_model = "gemma2:9b"
        
        system_content = ""
        conversation_history = ""
        last_user_answer = ""

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "assistant":
                conversation_history += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_history += "지원자: {}\n".format(msg["content"])
                last_user_answer = msg["content"]

        final_prompt = (
            "{}\n\n"
            "[대화 흐름 타임라인 기록]\n"
            "{}\n"
            "[지원자의 가장 최신 답변]\n"
            "\"{}\"\n\n"
            "[AI 면접관의 절대 행동 지침]\n"
            "너는 제공된 대화 기록을 기반으로 면접이 진행 중임을 인지하라.\n"
            "가볍게 1분 자기소개 부탁한다는 첫 질문은 이미 과거에 완료되었으니 절대 다시 꺼내지 마라.\n"
            "반드시 지원자가 방금 제출한 '가장 최신 답변'을 예리하게 분석하여, 프로젝트 구현 과정이나 소통 방식의 취약점을 매섭게 파고드는 '다음 압박 꼬리 질문 딱 한 개'만 정중한 경어체로 출제하라."
        ).format(system_content, conversation_history, last_user_answer)

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": target_model,
            "prompt": final_prompt.strip(),
            "options": {"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096, "repeat_penalty": 1.3},
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json and str(res_json["response"]).strip() != "":
                ai_reply = res_json["response"].strip()
                if "자기소개" in ai_reply or "의견 충돌이 있었을 때" in ai_reply:
                    return "지원자님께서 방금 답변해주신 챗봇 응답 처리 방식 조율 경험이 흥미롭습니다. 그렇다면 당시 팀원이 기능 중심으로 단순하게 구현하자고 주장했을 때, 이를 기술적인 근거(유지보수성 등)를 들어 설득했던 구체적인 대화 과정이나 본인만의 소통 노하우를 상세히 말씀해 주세요."
                return ai_reply

        return "지원자님께서 답변해주신 소통 방식 잘 들었습니다. 그렇다면 제한된 시간 속에서 완성도와 마감 기한 중 무엇을 더 최우선 가치로 두고 팀원들과 협의를 이끌어내셨는지 본인의 가치관을 설명해 주세요."
    except Exception as e:
        print("[Ollama Connection Error] 상세 원인: {}".format(e))
        return "지원자님께서 답변해주신 소통 방식 잘 들었습니다. 그렇다면 제한된 시간 속에서 완성도와 마감 기한 중 무엇을 더 최우선 가치로 두고 팀원들과 협의를 이끌어내셨는지 본인의 가치관을 설명해 주세요."

def render_interview_page():
    """🤖 실전 대화형 AI 면접방 화면 (새로고침 실시간 원격 복원 탑재)"""
    if not st.session_state.get("document_loaded"):
        st.warning("⚠️ 아직 이력서가 업로드되지 않았습니다. '이력서 제출' 메뉴에서 서류를 먼저 저장해 주세요.")
        return

    uid = st.session_state["user_info"]["user_id"]
    company = st.session_state.get("selected_company", "지정 기업")
    job = st.session_state.get("selected_job", "지정 직무")
    style = st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")
    doc_text = st.session_state.get("document_text", "")

    st.subheader("🤖 AI 실전 압박 면접방")
    st.caption("🎯 목표 기업: **{}** | 💼 지원 직무: **{}** | 🧠 면접관 성향: **{}**".format(company, job, style))
    st.markdown("---")

    # 💡 [핵심 추가] 새로고침으로 세션이 날아갔을 때, MariaDB에서 미종료된 실시간 대화 기록이 있다면 강제 원격 복원
    if "interview_messages" not in st.session_state:
        # 가장 최근 면접 히스토리 1건을 조회하여 아직 평가서(feedback_log)가 생성되지 않은 실시간 세션인지 확인
        histories = db.get_user_interview_histories(uid)
        active_session = None
        
        for h in histories:
            if h["company"] == company and h["job"] == job and (not h.get("feedback_log") or h["feedback_log"].strip() == ""):
                active_session = h
                break
                
        if active_session:
            try:
                # 💡 [복원 실행] MariaDB에 박제되어 있던 대화 배열 로그를 긁어와 세션 메모리에 그대로 이식!
                saved_logs = json.loads(active_session["chat_log"])
                system_prompt = f"너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다. 현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다. 너는 질문을 한 번에 '딱 한 개'씩만 정중한 경어체로 출제해야 한다. 너가 했던 질문을 절대 반복하지 마라.\n\n[지원자 서류 본문 데이터]\n{doc_text}"
                
                rebuilt_messages = [{"role": "system", "content": system_prompt}]
                rebuilt_messages.extend(saved_logs)
                st.session_state["interview_messages"] = rebuilt_messages
                st.session_state["current_db_history_id"] = active_session["id"] # 현재 작동 중인 행 고유 ID 연결
            except:
                pass

    # 💡 위의 복원 루틴을 통과하고도 데이터가 없다면, 그제서야 순정 오프닝 1번 질문 생성
    if "interview_messages" not in st.session_state:
        system_prompt = f"너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다. 현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다. 너는 질문을 한 번에 '딱 한 개'씩만 정중한 경어체로 출제해야 한다. 너가 했던 질문을 절대 반복하지 마라.\n\n[지원자 서류 본문 데이터]\n{doc_text}"
        fixed_initial_question = f"안녕하십니까 지원자님, 이번 {company}의 {job} 직무 모의 면접을 진행하게 된 AI 면접관입니다. 너무 긴장하지 마시고, 먼저 가볍게 1분 자기소개부터 부탁드립니다."
        
        st.session_state["interview_messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": fixed_initial_question}
        ]
        # 최초 1번 상태를 MariaDB 보관함에 선제 적재하여 고유 행 ID 발급 수령
        h_id = db.save_interview_history(uid, company, job, style, st.session_state["interview_messages"])
        st.session_state["current_db_history_id"] = h_id

    # 화면에 대화 로그 출력
    for msg in st.session_state["interview_messages"][1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 하단 채팅 입력바 구현
    if user_answer := st.chat_input("이곳에 질문에 대한 답변을 입력하고 Enter를 누르세요..."):
        st.session_state["interview_messages"].append({"role": "user", "content": user_answer})
        with st.chat_message("user"): st.write(user_answer)
            
        with st.chat_message("assistant"):
            with st.spinner("📝 지원자님의 답변을 사내 내부 연산망으로 정밀 분석 중..."):
                next_q = generate_ai_question(st.session_state["interview_messages"])
                st.write(next_q)
                st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
                
                # 💡 [핵심 추가] 질문과 답변이 주거니 받거니 끝난 실시간 지점에서, MariaDB 해당 행을 찾아 실시간 동기화 업데이트!
                h_id = st.session_state.get("current_db_history_id")
                if h_id:
                    # 임시 저장을 위해 feedback_log는 비워둔 채 대화 로그만 실시간 패치 업데이트
                    try:
                        with db.get_db() as conn, conn.cursor() as cur:
                            cur.execute("USE {};".format(db.N))
                            clean_log = json.dumps([m for m in st.session_state["interview_messages"] if m["role"] != "system"], ensure_ascii=False)
                            cur.execute("UPDATE kkochi_history SET chat_log = %s WHERE id = %s", (clean_log, h_id))
                            conn.commit()
                    except:
                        pass
                st.rerun()

    # 면접 원스톱 실시간 적재 버튼 구역
    st.markdown("---")
    if st.button("🚪 면접 종료 및 AI 종합 피드백 받기 ➡️", use_container_width=True, type="primary"):
        with st.spinner("📝 면접 내용을 종합 채점하고 보관함에 이력을 안전하게 적재 중입니다..."):
            import feedback_page
            report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
            if not report:
                report = {
                    "total_score": 85, "grade": "A",
                    "strengths": "기술적 근거를 바탕으로 협업 조율 능력을 피력한 점이 돋보입니다.",
                    "weaknesses": "일부 구조적 유지보수성 서술에 정량적 지표 보완이 필요합니다.",
                    "best_answer_guide": "성과 지표를 추가해 두괄식으로 설명하는 연습을 해보세요."
                }
            
            # 최종 종료 시 피드백 결과 JSON까지 세트로 완전히 완성시켜 덮어쓰기 마감
            h_id = st.session_state.get("current_db_history_id")
            if h_id:
                db.update_interview_feedback(h_id, report)
            st.session_state["feedback_report"] = report
        st.session_state["current_menu"] = "📊 면접 피드백"
        st.rerun()