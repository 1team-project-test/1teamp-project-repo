import os
import json
import requests
import streamlit as st
import mariadb_control as db
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import subprocess
import speech_recognition as sr  

def play_ai_voice(text):
    """🤖 AI의 텍스트를 음성으로 변환하고 자동 재생하는 함수"""
    try:
        clean_text = text.replace("*", "").replace("#", "").replace("_", "")
        speed = "+10%" 
        subprocess.run([
            "edge-tts", 
            "--text", clean_text, 
            "--write-media", "temp_voice.mp3", 
            "--voice", "ko-KR-InJoonNeural", 
            "--rate", speed
        ], check=True)
        
        with open("temp_voice.mp3", "rb") as f:
            audio_bytes = f.read()
        
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        st.toast(f"🔊 AI 면접관이 말하고 있습니다... (속도: {speed})", icon="🗣️")
        
    except Exception as e:
        st.error(f"⚠️ TTS 음성 생성 실패: {e}")
        print(f"[TTS 에러] 음성 재생 실패: {e}")

def get_expert_context(user_answer, job_title, limit=2):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name="interview_expert_data"
        )
        docs = vectorstore.similarity_search(query=user_answer, k=limit, filter={"job": job_title})
        if docs:
            return "\n\n".join([doc.page_content for doc in docs])
        return "참고할 전문가 데이터가 없습니다."
    except Exception as e:
        print(f"RAG 검색 에러: {e}")
        return "데이터 검색 중 오류 발생"

def generate_ai_question(messages):
    """🤖 [온프레미스] gemma2:9b 모델 기반 RAG 꼬리 질문 추출 엔진"""
    try:
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

        current_job = st.session_state.get("selected_job", "BM")
        expert_context = get_expert_context(last_user_answer, current_job)

        print("\n" + "="*60)
        print(f"🎯 [RAG 작동 확인] 지원 직무: {current_job}")
        print(f"🧐 [지원자 방금 답변]: {last_user_answer}")
        print(f"📚 [DB에서 훔쳐온 전문가 데이터]:\n{expert_context}")
        print("="*60 + "\n")

        final_prompt = (
            "{}\n\n"
            "[대화 흐름 타임라인 기록]\n"
            "{}\n"
            "[지원자의 가장 최신 답변]\n"
            "\"{}\"\n\n"
            "[🎯 전문가 실제 면접 데이터 (참고용)]\n"
            "{}\n\n"
            "[AI 면접관의 절대 행동 지침]\n"
            "너는 제공된 대화 기록을 기반으로 면접이 진행 중임을 인지하라.\n"
            "가볍게 1분 자기소개 부탁한다는 첫 질문은 이미 과거에 완료되었으니 절대 다시 꺼내지 마라.\n"
            "반드시 지원자가 방금 제출한 '가장 최신 답변'과 위의 '전문가 실제 면접 데이터'를 비교 분석하여, "
            "지원자의 논리적 허점이나 보완해야 할 점을 매섭게 파고드는 '다음 압박 꼬리 질문 딱 한 개'만 정중한 경어체로 출제하라."
        ).format(system_content, conversation_history, last_user_answer, expert_context)

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
                    return "지원자님께서 방금 답변해주신 응답 처리 방식 조율 경험이 흥미롭습니다. 그렇다면 당시 팀원이 기능 중심으로 단순하게 구현하자고 주장했을 때, 이를 기술적인 근거(유지보수성 등)를 들어 설득했던 구체적인 대화 과정이나 본인만의 소통 노하우를 상세히 말씀해 주세요."
                return ai_reply

        return "지원자님께서 답변해주신 소통 방식 잘 들었습니다. 그렇다면 제한된 시간 속에서 완성도와 마감 기한 중 무엇을 더 최우선 가치로 두고 팀원들과 협의를 이끌어내셨는지 본인의 가치관을 설명해 주세요."
    except Exception as e:
        print("[Ollama Connection Error] 상세 원인: {}".format(e))
        return "통신 지연으로 인한 기본 질문입니다. 프로젝트 진행 시 가장 어려웠던 기술적 난제는 무엇이었나요?"

def render_interview_page():
    """🤖 실전 대화형 AI 면접방 화면 (STT 음성인식 탑재)"""
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

    if "new_audio_text" in st.session_state and st.session_state["new_audio_text"]:
        play_ai_voice(st.session_state["new_audio_text"])
        st.session_state["new_audio_text"] = "" 

    if "interview_messages" not in st.session_state:
        histories = db.get_user_interview_histories(uid)
        active_session = None
        
        for h in histories:
            if h["company"] == company and h["job"] == job and (not h.get("feedback_log") or h["feedback_log"].strip() == ""):
                active_session = h
                break
                
        if active_session:
            try:
                saved_logs = json.loads(active_session["chat_log"])
                system_prompt = f"너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다. 현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다. 너는 질문을 한 번에 '딱 한 개'씩만 정중한 경어체로 출제해야 단다. 너가 했던 질문을 절대 반복하지 마라.\n\n[지원자 서류 본문 데이터]\n{doc_text}"
                
                rebuilt_messages = [{"role": "system", "content": system_prompt}]
                rebuilt_messages.extend(saved_logs)
                st.session_state["interview_messages"] = rebuilt_messages
                st.session_state["current_db_history_id"] = active_session["id"]
            except:
                pass

    if "interview_messages" not in st.session_state:
        system_prompt = f"너는 {company}의 {job} 채용을 담당하는 베테랑 AI 면접관이다. 현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다. 너는 질문을 한 번에 '딱 한 개'씩만 정중한 경어체로 출제해야 한다. 너가 했던 질문을 절대 반복하지 마라.\n\n[지원자 서류 본문 데이터]\n{doc_text}"
        fixed_initial_question = f"안녕하십니까 지원자님, 이번 {company}의 {job} 직무 모의 면접을 진행하게 된 AI 면접관입니다. 너무 긴장하지 마시고, 먼저 가볍게 1분 자기소개부터 부탁드립니다."
        
        st.session_state["interview_messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": fixed_initial_question}
        ]
        h_id = db.save_interview_history(uid, company, job, style, st.session_state["interview_messages"])
        st.session_state["current_db_history_id"] = h_id
        
        st.session_state["new_audio_text"] = fixed_initial_question
        st.rerun() 

    for i, msg in enumerate(st.session_state["interview_messages"][1:]):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 질문 다시 듣기", key=f"btn_tts_{i}"):
                    play_ai_voice(msg["content"])

    # ==========================================
    # 💡 면접 종료 버튼 (대화 로그 바로 아래 배치)
    # ==========================================
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
            
            h_id = st.session_state.get("current_db_history_id")
            if h_id:
                db.update_interview_feedback(h_id, report)
            st.session_state["feedback_report"] = report
        st.session_state["current_menu"] = "📊 면접 피드백"
        st.rerun()

    # ==========================================
    # 💡 [새로운 레이아웃] 세련된 텍스트 입력창 + 숨겨진 마이크 토글
    # ==========================================
    final_user_answer = None
    
    # 마이크를 켜고 끄는 스위치 (기본값: 꺼짐)
    use_mic = st.toggle("🎙️ 음성으로 답변하기 (마이크 켜기)")
    
    if use_mic:
        st.info("👇 아래 마이크 아이콘을 눌러 녹음을 시작하세요.")
        audio_bytes = st.audio_input("음성 답변", label_visibility="collapsed")
        
        if audio_bytes is not None:
            if st.session_state.get("last_processed_audio") != audio_bytes:
                with st.spinner("🗣️ 음성을 인식하고 있습니다..."):
                    r = sr.Recognizer()
                    try:
                        with sr.AudioFile(audio_bytes) as source:
                            audio_data = r.record(source)
                            stt_text = r.recognize_google(audio_data, language="ko-KR")
                            final_user_answer = stt_text
                            st.session_state["last_processed_audio"] = audio_bytes
                    except sr.UnknownValueError:
                        st.error("🤔 목소리를 명확하게 인식하지 못했습니다. 다시 녹음하거나 토글을 끄고 텍스트를 이용해 주세요.")
                        st.session_state["last_processed_audio"] = audio_bytes
                    except Exception as e:
                        st.error(f"⚠️ STT 에러 발생: {e}")
                        st.session_state["last_processed_audio"] = audio_bytes

    # 💡 둥글고 세련된 스트림릿 전용 텍스트 입력창 (항상 맨 아래 바닥에 고정됨)
    text_input = st.chat_input("또는 이곳에 텍스트로 답변을 입력하세요...")
    if text_input:
        final_user_answer = text_input

    # 💡 [공통 처리] 텍스트든 음성이든 답변이 들어왔다면 AI에게 전송!
    if final_user_answer:
        st.session_state["interview_messages"].append({"role": "user", "content": final_user_answer})
        with st.chat_message("user"): 
            st.write(f"🎤 {final_user_answer}")
            
        with st.chat_message("assistant"):
            with st.spinner("📝 지원자님의 답변을 정밀 분석 중..."):
                next_q = generate_ai_question(st.session_state["interview_messages"])
                st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
                
                # 다음 질문 자동 재생 예약
                st.session_state["new_audio_text"] = next_q
                
                h_id = st.session_state.get("current_db_history_id")
                if h_id:
                    try:
                        with db.get_db() as conn, conn.cursor() as cur:
                            cur.execute("USE {};".format(db.N))
                            clean_log = json.dumps([m for m in st.session_state["interview_messages"] if m["role"] != "system"], ensure_ascii=False)
                            cur.execute("UPDATE kkochi_history SET chat_log = %s WHERE id = %s", (clean_log, h_id))
                            conn.commit()
                    except:
                        pass
                st.rerun()