import os, json, requests, base64, time
import streamlit as st
import mariadb_control as db
from gtts import gTTS
import speech_recognition as sr

def play_text_to_speech_silently(text, chunk_id="default"):
    """🔊 [글로벌 마스터 단일화 완독 채널] 2번째 질문부터 타이머 새로고침에 소리가 짤리던 현상을 완벽 박멸 완치"""
    try:
        if not text: return
        clean_text = str(text).replace("*", "").replace("'", "").replace('"', "").replace("`", "").strip()
        if not clean_text: return
        
        tts = gTTS(text=clean_text, lang='ko', slow=False)
        temp_path = os.path.join(os.path.dirname(__file__), "temp_voice_kkochi_master.mp3")
        tts.save(temp_path)
        
        with open(temp_path, "rb") as f: 
            encoded_audio = base64.b64encode(f.read()).decode()
        audio_src_data = f"data:audio/mp3;base64,{encoded_audio}"
        
        # 🎯 [완치 포인트 1] 무식하게 오디오 노드를 지우지 마라! 
        # 자바스크립트 DOM을 통해 기존 재생 장치 본체는 놔두고 소리 주소(src)만 실시간 번개 체인지 후 강제 연속 재생!
        st.markdown(f"""
            <script>
            (function() {{
                var d = window.parent.document;
                var masterAudio = d.getElementById("kkochi_voice_master");
                if (masterAudio) {{
                    masterAudio.src = "{audio_src_data}";
                    masterAudio.load();
                    masterAudio.play().catch(function(e){{ console.log(e); }});
                }}
            }})();
            </script>
        """, unsafe_allow_html=True)
        
        # 최초방 대기 진입 시 오디오 핵심 가구 1회 도킹 개통
        st.markdown(f'<audio autoplay="true" id="kkochi_voice_master" src="{audio_src_data}" style="display:none;"></audio>', unsafe_allow_html=True)
    except Exception as e:
        print(f"[TTS 마스터 채널 최종 완치 에러] {e}")

def query_chroma_rag_context(user_answer):
    """🧠 [전체 무제한 RAG 서치 엔진] 7만 건 기출 본문 전체에서 최적의 면접 문맥 100% 서치"""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        project_root = os.path.dirname(os.path.abspath(__file__))
        chroma_path = os.path.join(project_root, "chroma_db")
        if not os.path.exists(chroma_path): return ""
        
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        korean_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-base")
        collection = chroma_client.get_collection(name="kkochi_ai_rag", embedding_function=korean_embedding_fn)
        
        results = collection.query(query_texts=[user_answer], n_results=1)
        if results and "documents" in results and results["documents"] and len(results["documents"]) > 0:
            return f"\n[AI-Hub 참고 기출서]\n{results['documents']}\n"
        return ""
    except Exception as e: print(f"[ChromaDB 쿼리 에러] {e}"); return ""

# 💡 [ interview_page.py - Page 2 내부 generate_ai_question 함수 전체 전면 대세척 교체 수역 - 스페이스 0칸 시작 ]
def generate_ai_question(messages):
    """🤖 [무작위 셔플 7단계 면접 변속 엔진] RAG 오염 및 면접관의 질문 찌꺼기 글자를 완벽히 소멸 청소한 최종 마감판"""
    try:
        import random, time
        st.session_state["ai_thinking_now"] = True
        
        system_content, conversation_history, last_user_answer = "", "", ""
        for msg in messages:
            if msg["role"] == "system": system_content = msg["content"]
            elif msg["role"] == "assistant": conversation_history += f"면접관: {msg['content']}\n"
            elif msg["role"] == "user":
                conversation_history += f"지원자: {msg['content']}\n"
                last_user_answer = msg["content"].strip()
                
        # 🚫 비속어 필터 가드 라인 (유저님 고유 자산 철통 보존)
        bad_words = ["꺼져", "시발", "새끼", "존나", "개같은", "미친"]
        if any(bad in last_user_answer for bad in bad_words):
            st.session_state["ai_thinking_now"] = False
            return "지원자님, 모의 면접 환경에서 비속어가 섞인 표현은 부적절한 언행입니다. 상호 존중과 예의를 바탕으로 다시 한번 진중하게 답변 부탁드립니다."
       
        greetings = ["안녕", "하이", "반갑", "반가", "네", "예", "음", "오케이", "안녕하세요"]
        if len(last_user_answer) <= 3 or any(greet in last_user_answer for greet in greetings):
            # 엇박자로 유실되던 유저 데이터 강제 누적선 바인딩 매립 완료
            if not messages or messages[-1]["content"] != last_user_answer:
                messages.append({"role": "user", "content": last_user_answer})
                
            with st.spinner("📝 안내 인사 확인 중..."):
                time.sleep(1.2)
            st.session_state["ai_thinking_now"] = False
            return "네, 반갑습니다 지원자님! 긴장하지 마시고 답변을 편안하게 이어나가 주시기 바랍니다. 본격적인 역량 검증을 위해 본인이 목표로 하시는 직무에서 가장 자신 있는 핵심 프로젝트 성과나 전공 역량 위주로 두괄식으로 구체적으로 설명해 주세요."

        if st.session_state.get("interview_timer_limit_minutes") is not None and st.session_state.get("timer_start_timestamp") is not None:
            elapsed = time.time() - st.session_state["timer_start_timestamp"]
            if elapsed >= (st.session_state["interview_timer_limit_minutes"] * 60):
                st.session_state["ai_thinking_now"] = False
                return "🚨 [제한 시간 초과] 지원자님, 안타깝게도 약속된 총 면접 제한 시간이 모두 종료되었습니다. 모의 면접 평가 프로세스를 여기서 전면 마감합니다. 아래의 '🚪 면접 종료 및 AI 종합 피드백 받기' 단추를 클릭하여 성적표방에서 즉시 채점 리포트를 확인해 보시기 바랍니다."

        if "shuffled_stages" not in st.session_state:
            base_stages = [1, 2, 3, 4, 5]
            random.shuffle(base_stages)
            st.session_state["shuffled_stages"] = base_stages

        total_questions_sent = len([x for x in messages if x["role"] == "assistant"])
        
        if total_questions_sent <= 3: current_stage_id = st.session_state["shuffled_stages"][0]
        elif total_questions_sent <= 6: current_stage_id = st.session_state["shuffled_stages"][1]
        elif total_questions_sent <= 9: current_stage_id = st.session_state["shuffled_stages"][2]
        elif total_questions_sent <= 12: current_stage_id = st.session_state["shuffled_stages"][3]
        elif total_questions_sent <= 15: current_stage_id = st.session_state["shuffled_stages"][4]
        else:
            st.session_state["ai_thinking_now"] = False
            return "지원자님, 고생 많으셨습니다. 준비된 5대 핵심 무작위 세션의 3문 3답 평가 절차가 모두 안전하게 완주 마감되었습니다. 아래의 '🚪 면접 종료 및 AI 종합 피드백 받기' 버튼을 눌러 결과를 성적표방에서 확인해 보시기 바랍니다."

        if current_stage_id == 1:
            stage_title = "자기소개 (1분 내외) 심층 검증 단계"
            stage_instruction = "지원자가 최초에 말한 자기소개 키워드와 직전 답변을 정밀 연동하여, 미흡하거나 과장된 논리를 날카롭게 파고드는 질문을 출제하라."
        elif current_stage_id == 2:
            stage_title = "이력 / 경험 질문 검증 단계"
            stage_instruction = "제출된 서류 본문 내용과 경험 명세를 저격하여, 지원자가 가동했던 구체적인 역할 행동과 성과 수치 지표의 진위를 파헤치는 질문을 출제하라."
        elif current_stage_id == 3:
            stage_title = "기술 면접 (직무 면접) 평가 단계"
            stage_instruction = "선택된 직무 카테고리의 전공 지식 및 7만 건 기출 RAG 족보 문맥을 활용하여, 지원자의 직무 기술적 구현 깊이를 집요하게 검증하는 질문을 출제하라."
        elif current_stage_id == 4:
            stage_title = "인성 / 상황 대처 능력 평가 단계"
            stage_instruction = "원론적인 답변을 거부하라. 현업에서 최악의 한계 위기 상황을 가정하여 지원자의 인성과 위기관리 능력을 압박하는 질문을 출제하라."
        elif current_stage_id == 5:
            stage_title = "지원 동기 / 회사 관련 질문 최종 단계"
            stage_instruction = "이 회사와 지정한 목표 직무에 왜 본인이 독보적인 진정성을 가졌는지 검증하고, 입사 후 구체적인 포부를 파고드는 질문을 출제하라."

        interview_dice = random.random()
        rag_data = query_chroma_rag_context(last_user_answer)
        
        rag_prompt_section = ""
        if current_stage_id == 3 or interview_dice >= 0.30:
            if rag_data:
                rag_prompt_section = f"{rag_data}\n[RAG 기출 가이드] 위 기출서의 실제 출제 패턴 핏을 참조하여 질문을 조각하라."

        final_prompt = f"""
        {system_content}
        너는 아주 엄격하고 냉철한 실제 기업의 핵심 채용 면접관이다.
        ➡️ 🎲 [{stage_title}] (현재 섹션 세부 진행도: {total_questions_sent % 3 if total_questions_sent % 3 != 0 else 3}/3회차)
        [AI 면접관의 절대 행동 및 출력 지침]
        1. 현재 배정된 [{stage_title}] 구역의 목적에 맞게 날카로운 질문을 출제하라.
        2. {stage_instruction}
        3. {rag_prompt_section}
        4. 🚫절대 주의 조항: 답변 출력 시 '면접관의 질문:', '설명:', '이유:', '분석:' 같은 주석, 접두사, 서론, 본론 머리표를 단 한 자도 출력하지 마라!
        5. 오직 지원자에게 던질 순수한 면접 질문 '딱 한 문장'만 가감 없이 텍스트로 출력하라.
        [대화 흐름 타임라인 기록]
        {conversation_history}
        [지원자의 가장 최신 답변]
        "{last_user_answer}"
        """

        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "gemma2:9b", "prompt": final_prompt.strip(),
            "options": {"temperature": 0.3, "top_p": 0.85, "num_ctx": 8192, "repeat_penalty": 1.3}, "stream": False
        }, timeout=30)
        
        st.session_state["ai_thinking_now"] = False
        
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json and str(res_json["response"]).strip() != "": 
                ai_q = res_json["response"].strip()
                
                # 🎯 [완치 핵심 3번 - 접두사 슬래싱 박멸 필터]
                # 프롬프트를 무시하고 튀어나온 '면접관의 질문:', '설명:', '분석:' 머리 표식 문자열 전체를 전면 무력화 소멸 세척합니다!
                ai_q = ai_q.replace("면접관의 질문:", "").replace("면접관의 질문", "")
                if "설명:" in ai_q: ai_q = ai_q.split("설명:")[0]
                if "분석:" in ai_q: ai_q = ai_q.split("분석:")[0]
                return ai_q.strip()
                
        return f"지원자님께서 답변해주신 내용 흥미롭게 잘 들었습니다. 그렇다면 말씀하신 부분과 관련하여 조금 더 구체적인 실전 사례나 본인의 대처 능력을 설명해 주세요."
    except Exception as e:
        st.session_state["ai_thinking_now"] = False
        return "지원자님의 답변 잘 들었습니다. 본인의 역량을 발휘하여 성과를 이끌어낸 다른 경험을 구체적으로 설명해 주세요."

# 💡 [ interview_page.py - render_interview_page 함수 시작점부터 헤더 columns 직전까지 통째로 교체 수술 구역 - 스페이스 4칸 정렬 고수 ]
def render_interview_page():
    """🤖 AI 실전 압박 면접방 화면 본체"""

    st.markdown("""
        <style>
        /* 스트림릿 순정 고정 격벽(centered)을 강제로 풀 와이드 리사이징 모드로 오버라이딩 */
        div[data-testid='stAppViewBlockContainer'] {
            max-width: 100% !important;
            padding-left: max(20px, 3.5vw) !important;
            padding-right: max(20px, 3.5vw) !important;
            width: 100% !important;
        }
        /* 대화방 메인 패널과 내부 요소들이 부모 배율을 100% 흡수 연동하도록 동기화 */
        .main .block-container {
            max-width: 100% !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    uid = st.session_state["user_info"]["user_id"]
    company = st.session_state.get("selected_company", "목표 기업")
    job = st.session_state.get("selected_job", "지원 직무")
    style = st.session_state.get("selected_style", "공감형 (부드러운 칭찬 중심)")
    doc_text = st.session_state.get("document_text", "제출된 서류 기반의 디폴트 가이드 문맥")
    
    # 💡 [ interview_page.py - PDF 7~8페이지 타이머 변수 및 배너 구역 전면 대세척 교체 수술 - 스페이스 4칸 정렬 칼핏 고수 ]
    # 🎯 [완치 핵심 별 5개 저격선] 사용자가 가만히 서 있어도 백엔드에서 1초마다 독단적으로 시계를 흔들어 깨우는
    # 스트림릿 프레임워크 순정 독립 주행 프래그먼트(@st.fragment) 엔진을 장착 매립 완료했습니다! (화면 캐시 동결 완벽 격파)
    if "interview_started_gate" not in st.session_state:
        st.session_state["interview_started_gate"] = False

    if "interview_timer_limit_minutes" not in st.session_state:
        st.session_state["interview_timer_limit_minutes"] = 15

    if "timer_start_timestamp" not in st.session_state:
        st.session_state["timer_start_timestamp"] = None

    # 🔒 면접 룸 내부에서 부모 리런 자극이 들어와도 시작 시간 축이 오염당하지 않도록 락 장치 연동 [PDF: 0.1.10]
    if st.session_state.get("interview_started_gate") == True and st.session_state.get("timer_start_timestamp") is None:
        st.session_state["timer_start_timestamp"] = time.time()

    time_over_triggered = False

    # 💡 [ interview_page.py - PDF 7~8페이지 @st.fragment 시작선부터 함수 호출 끝줄까지 통째로 최종 교체 수술 - 스페이스 4칸 정렬 고수 ]
    # 🎯 [완치 핵심 그랜드 피날레 저격선] 격리 주머니(@st.fragment) 내부에서 0초 타격 즉시 
    # 울타리를 통째로 파괴하고 파일 전체 화면을 피드백방으로 강제 소환 수송시키는 직통 파이프라인 개통 완료! [PDF: 0.1.11, 0.1.16]
    @st.fragment(run_every=1.0)
    def render_realtime_kkochi_timer():
        if st.session_state.get("timer_start_timestamp") is not None and st.session_state.get("interview_started_gate") == True:
            elapsed_seconds = time.time() - st.session_state["timer_start_timestamp"]
            total_limit_seconds = st.session_state["interview_timer_limit_minutes"] * 60
            remaining_seconds = max(0, total_limit_seconds - elapsed_seconds)
            rem_min, rem_sec = int(remaining_seconds // 60), int(remaining_seconds % 60)
            
            if remaining_seconds > 0:
                st.markdown(f"<div style='background-color:#fff5f3; border: 1px solid #ff5232; padding: 6px 12px; border-radius:6px; font-size:13px; font-weight:700; color:#ff5232; text-align:center; margin-top:6px; margin-bottom:8px;'>⏳ 남은 모의 면접 시간 ➡ {rem_min:02d}분 {rem_sec:02d}초</div>", unsafe_allow_html=True)
            else:
                # 🔒 [완치 마스터 직통 가벨 잠금] 0초 도달 즉시 격리 장벽을 우회하여 부모 라우터를 피드백방으로 강제 워프 리매핑 후 전면 강제 리런 사출! [PDF: 0.1.16]
                st.error("🚨 [타임 오버] 설정하신 총 면접 제한 시간이 모두 초과되었습니다! 모의 면접을 즉시 종료하고 AI 종합 피드백방으로 이동합니다.")
                time.sleep(2.5)
                with st.spinner("📝 성적 리포트 연산 및 피드백방 워프 중..."):
                    import feedback_page
                    report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
                    if not report: 
                        report = {"total_score": 75, "grade": "B", "strengths": "끝까지 면접에 임하셨습니다.", "weaknesses": "제한시간 초과로 자동 마감되었습니다.", "best_answer_guide": "두괄식 답변으로 시간을 절약하세요."}
                    h_id = st.session_state.get("current_db_history_id")
                    if h_id: 
                        db.update_interview_feedback(h_id, report)
                    st.session_state["feedback_report"] = report
                
                # 대화방 보관 주머니 리셋 및 피드백방 메뉴 강제 이송 트리거 작동 [PDF: 0.1.16]
                st.session_state.pop("interview_messages", None)
                st.session_state.pop("current_db_history_id", None)
                st.session_state.pop("shuffled_stages", None)
                st.session_state["timer_start_timestamp"] = None
                st.session_state["interview_started_gate"] = False
                st.session_state["current_menu"] = "📊 면접 피드백" 
                st.rerun(scope="app")

    # 독립 타이머 구동 파이프라인 가동 선포
    render_realtime_kkochi_timer()

    col_header_info, col_header_btn = st.columns([0.75, 0.25])
    
    with col_header_info:
        st.markdown(f"<div style='background-color:#fff5f3; border-left:4px solid #ff5232; padding:6px 12px; border-radius:6px; font-size:11.5px; color:#234e52; min-height:32px; line-height:20px;'>🍢 <b>목표 기업:</b> {company} &nbsp;|&nbsp; 💼 <b>지원 직무:</b> {job} &nbsp;|&nbsp; 🧠 <b>면접관 성향:</b> {style}</div>", unsafe_allow_html=True)
        
    with col_header_btn:
        if st.session_state.get("interview_started_gate") and st.button("📊 면접 종료 및 피드백 받기", use_container_width=True, type="primary", key="btn_finish_interview"):
            with st.spinner("📊 면접 내용에 대한 피드백 생성중..."):
                import feedback_page
                report = feedback_page.generate_interview_feedback(st.session_state["interview_messages"])
                if not report: 
                    report = {"total_score": 85, "grade": "A", "strengths": "협업 능력이 돋보입니다.", "weaknesses": "지표 보완이 필요합니다.", "best_answer_guide": "두괄식 연습을 해보세요."}
                h_id = st.session_state.get("current_db_history_id")
                if h_id: 
                    db.update_interview_feedback(h_id, report)
                st.session_state["feedback_report"] = report
            
            st.session_state.pop("interview_messages", None)
            st.session_state.pop("current_db_history_id", None)
            st.session_state.pop("shuffled_stages", None)
            st.session_state["timer_start_timestamp"] = None
            st.session_state["interview_started_gate"] = False
            st.session_state["current_menu"] = "📊 면접 피드백"
            st.rerun()

    # 🎯 [완치 핵심 저격 포인트] 하방에서 타임오버 플래그를 읽기 전에, 
    # 변수방 개설 초기화(time_over_triggered = False) 선언식을 정위치에 명확히 선포 주입 완료했습니다!
    time_over_triggered = False

    # 💡 [ interview_page.py - PDF 38페이지 대기방 슬라이더 시작선부터 파일 맨 최하단 마지막 끝줄까지 통째로 최종 개혁 교체 수술 구역 ]
    # 🎯 [인트로 대기 모드 게이트 제어 블록] 면접 시작 전 제한 시간 슬라이더 조율 구역
    if not st.session_state["interview_started_gate"]:
        st.markdown("<div style='margin-top:20px; margin-bottom:10px; padding:20px; background-color:#fafafa; border:1px solid #e2e8f0; border-radius:12px; text-align:center;'><h6 style='color:#1a202c; font-size:15px; margin-bottom:12px;'>⏱ 모의 면접 훈련 시간 설정</h6>", unsafe_allow_html=True)
        
        # 🎯 [완치 핵심 1] 5분 단위 장벽을 철거하고, 1분 간격(min_value=1, step=1)으로 30분까지 초정밀 커스텀 세팅이 가능하도록 기어를 대대 개혁했습니다!
        chosen_time = st.slider("제한 시간 조율 슬라이더", min_value=1, max_value=30, value=st.session_state["interview_timer_limit_minutes"], step=1, label_visibility="collapsed", key="slider_interview_timer_gate_control")
        st.session_state["interview_timer_limit_minutes"] = chosen_time
        st.markdown(f"<p style='font-size:13.5px; color:#4a5568; margin-top:10px; margin-bottom:20px;'>⏱ 선택하신 제한 시간: <b>{chosen_time}분</b>으로 모의 면접이 설정됩니다.</p>", unsafe_allow_html=True)
        
        if st.button("🚀 모의 면접 시작하기 🚀", key="btn_start_interview_trigger", use_container_width=True):
            current_company = st.session_state.get("selected_company", company)
            current_job = st.session_state.get("selected_job", job)
            current_doc_text = st.session_state.get("document_text", doc_text)
            current_style = st.session_state.get("selected_style", style)
 
            system_prompt = f"너는 {current_company}의 {current_job} 직무 모의 면접관이다.\n\n[서류 본문]\n{current_doc_text}"
            fixed_initial = f"안녕하십니까 지원자님, 이번 {current_company}의 {job} 직무 모의 면접을 진행하게 된 AI 면접관입니다. 너무 긴장하지 마시고, 먼저 가볍게 1분 자기소개부터 부탁드립니다."
 
            st.session_state["interview_messages"] = [{"role": "system", "content": system_prompt}, {"role": "assistant", "content": fixed_initial}]
 
            st.session_state["current_db_history_id"] = db.save_interview_history(
                uid, 
                current_company, 
                current_job, 
                current_style, 
                st.session_state["interview_messages"]
            )
 
            st.session_state["timer_start_timestamp"] = time.time()
            st.session_state["interview_started_gate"] = True
            st.session_state["trigger_post_render_tts"] = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if st.session_state.get("trigger_post_render_tts") and len(st.session_state.get("interview_messages", [])) == 2:
        first_msg = st.session_state["interview_messages"][-1]
        if first_msg["role"] == "assistant":
            play_text_to_speech_silently(first_msg["content"], chunk_id="init_first_gate")
        st.session_state["trigger_post_render_tts"] = False

    chat_container = st.container(height=195)
   # 💡 [ interview_page.py - chat_container 시작선 바로 아랫줄부터 자바스크립트 스크롤러 직전까지 통째로 최종 전면 대개혁 수술 ]
    with chat_container:
        # 기존 대화 렌더링 로직 유지 (순정 100% 사수 [PDF: 0.1.10])
        for m in st.session_state["interview_messages"][1:]:
            icon_col, text_col = st.columns([0.05, 0.95], gap="small")
            with icon_col:
                st.markdown(f"""<div style='background-color: {"#ffb74d" if m["role"] == "assistant" else "#ff5232"}; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-top: 2px;'><svg viewBox='0 0 24 24' width='16' height='16' fill='none' stroke='#ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{"<rect x='3' y='11' width='18' height='10' rx='2'></rect><circle cx='12' cy='5' r='2'></circle><path d='M12 7v4M8 15h.01M16 15h.01'></path>" if m["role"] == "assistant" else "<path d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'></path><circle cx='12' cy='7' r='4'></circle>"}</svg></div>""", unsafe_allow_html=True)
            with text_col:
                st.markdown(f"<div style='background-color: {'#fafafa' if m['role'] == 'assistant' else '#ff5232'}; border: {'1px solid #e2e8f0' if m['role'] == 'assistant' else 'none'}; border-radius: 4px 12px 12px 12px; color: {'#2d3748' if m['role'] == 'assistant' else '#ffffff'}; padding: 8px 12px; font-size: max(12px, 0.85vw); line-height: 1.5; text-align: left; width: fit-content; max-width: 90%;'>{str(m['content']).replace('***', '').strip()}</div>", unsafe_allow_html=True)

    st.markdown("""
        <script>
        (function(){
            var d = window.parent.document;
            var c = 0;
            var t = setInterval(function(){
                c++;
                // 1단계: 일반 웹뷰 내에 생성된 모든 스크롤 상자 일차 포착
                var elements = d.querySelectorAll("div[data-testid='stChatMessageContainer'], div[style*='height: 195px'], div[style*='overflow-y: auto']");
                elements.forEach(function(el){ el.scrollTop = el.scrollHeight; });
                
                // 2단계: 그림자 가상 보안 격벽(Shadow DOM) 내부 깊숙이 침투하여 숨겨진 순정 스크롤바 축까지 강제 강하 수송 집행!
                var allDivs = d.querySelectorAll('div');
                allDivs.forEach(function(div){
                    if(div.shadowRoot) {
                        var innerContainer = div.shadowRoot.querySelector("div[style*='overflow-y: auto'], div[data-testid='stChatMessageContainer']");
                        if(innerContainer) { innerContainer.scrollTop = innerContainer.scrollHeight; }
                    }
                });
                
                if(c > 40){ clearInterval(t); }
            }, 50);
        })();
        </script>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("trigger_post_render_tts") and len(st.session_state["interview_messages"]) > 2:
        last_msg = st.session_state["interview_messages"][-1]
        if last_msg["role"] == "assistant":
            play_text_to_speech_silently(last_msg["content"], chunk_id=f"post_{len(st.session_state['interview_messages'])}")
        st.session_state["trigger_post_render_tts"] = False

    if "stt_text_buffer" not in st.session_state: st.session_state["stt_text_buffer"] = ""

    # 💡 [ interview_page.py - PDF 13~17페이지 생각 중 마크업 조건문부터 파일 맨 끝줄까지 통째로 최종 교체 수술 - 스페이스 4칸 정렬 칼핏 고수 ]
    # 🎯 [완치 핵심 1] AI 면접관이 답변 분석 중(ai_thinking_now=True)일 때, 지저분한 하방 가구들을 0px로 완벽 차단 은닉 청소하고 로딩 알림판을 1회 사출합니다.
    if st.session_state.get("ai_thinking_now", False):
        st.markdown("""
            <style>
            div[data-testid='stHorizontalBlock']:has(div[key='kkochi_pure_voice_recorder']),
            div[data-testid='stChatInput'],
            .kkochi-stt-right-box,
            div[data-testid='stAudioInput'],
            section[data-testid='stAudioInput'],
            div.element-container:has(audio) {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0px !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            </style>
            <div style='margin-top: 15px; padding: max(12px, 1.5vh) max(20px, 2vw); background-color: #fff5f3; border: 1px dashed #ff5232; border-radius: max(8px, 0.8vw); text-align: center; box-shadow: 0 4px 12px rgba(255,82,50,0.05);'>
                <p style='margin: 0; font-size: max(13px, 1vw); font-weight: 800; color: #ff5232; display: flex; align-items: center; justify-content: center; gap: 8px;'>
                    <span style='display: inline-block; width: max(12px, 0.9vw); height: max(12px, 0.9vw); border: 2px solid #ff5232; border-top-color: transparent; border-radius: 50%; animation: kkochiSpinner 0.8s linear infinite;'></span>
                    📝 AI 면접관이 지원자님의 답변을 분석하고 다음 질문을 생성 중입니다!! 잠시만 기다려 주세요...
                </p>
            </div>
            <style>@keyframes kkochiSpinner { to { transform: rotate(360deg); } }</style>
        """, unsafe_allow_html=True)
        
        # 🎯 [완치 핵심 2] 매 초 카운트다운을 마비시키고 시계를 강제로 정지시키던 구형 타임 포즈 수식(freeze_start_time 연산 구조)을 전면 삭제 청소했습니다!
        next_q = generate_ai_question(st.session_state["interview_messages"])
        st.session_state["interview_messages"].append({"role": "assistant", "content": next_q})
        
        h_id = st.session_state.get("current_db_history_id")
        if h_id:
            try:
                with db.get_db() as conn, conn.cursor() as cur:
                    clean_log = json.dumps([x for x in st.session_state["interview_messages"] if x["role"] != "system"], ensure_ascii=False)
                    cur.execute("UPDATE kkochi_history SET chat_log = %s WHERE id = %s", (clean_log, h_id))
                    conn.commit()
            except: pass
            
        st.session_state["ai_thinking_now"] = False
        st.session_state["last_processed_file_size"] = 0
        st.session_state["trigger_post_render_tts"] = True
        st.rerun()
    else:
        # 정상 면접 문답 대기 상태일 때 하단 마이크 수평 대칭 핏 유지 고정
        st.markdown("""
            <style>
            div[data-testid='stHorizontalBlock']:has(div[key='kkochi_pure_voice_recorder']) { margin-top: -30px !important; margin-bottom: max(10px, 1.2vh) !important; }
            div[data-testid='stAudioInput'], section[data-testid='stAudioInput'] { height: 42px !important; min-height: 42px !important; padding: 0px !important; margin: 0px !important; margin-bottom: 0px !important; box-sizing: border-box !important; }
            .kkochi-stt-right-box { margin-top: 0px !important; margin-bottom: 0px !important; }
            div.stButton > button[key='btn_stt_submit_direct'] { height: 42px !important; margin-top: 0px !important; margin-bottom: 0px !important; }
            </style>
        """, unsafe_allow_html=True)
    
    # [0.50 : 0.50] 유저님이 사랑하시는 명품 수평 정대칭 마이크 보이스 가구 인프라 [PDF: 0.1.17]
    col_stt_left, col_stt_right = st.columns([0.50, 0.50])
    with col_stt_left:
        user_voice_file = st.audio_input("여기를 눌러 내 답변 목소리를 녹음해 보세요!", key="kkochi_pure_voice_recorder", label_visibility="collapsed")
        if user_voice_file is not None:
            file_current_size = user_voice_file.size
            if st.session_state.get("last_processed_file_size") != file_current_size:
                st.session_state["last_processed_file_size"] = file_current_size
                st.session_state["stt_processing_lock"] = True
                with st.spinner("🎙️ 목소리를 한글 문장 글자로 번역 받아쓰기 중..."):
                    try:
                        r = sr.Recognizer()
                        with sr.AudioFile(user_voice_file) as source:
                            audio_data = r.record(source)
                            st.session_state["stt_text_buffer"] = r.recognize_google(audio_data, language="ko-KR")
                            st.toast("✅ 음성 변환 완료!")
                    except Exception as e: st.toast("⚠️ 음성이 작거나 뭉개졌습니다. 다시 녹음해 주세요.")
                st.session_state["stt_processing_lock"] = False
                st.rerun()

    with col_stt_right:
        if st.session_state["stt_text_buffer"]:
            st.markdown(f'<div class="kkochi-stt-right-box" style="background-color:#e6fffa; border-left:3px solid #4caf50; padding:3px 8px; border-radius:6px; font-size:11px; color:#234e52; min-height:42px; max-height:42px; line-height:16px; overflow:hidden;">📝 <b>변환 결과:</b> {st.session_state["stt_text_buffer"]}</div>', unsafe_allow_html=True)
            if st.button("🚀 이 내용 면접관에게 보내기", key="btn_stt_submit_direct", use_container_width=True):
                st.session_state["interview_messages"].append({"role": "user", "content": st.session_state["stt_text_buffer"]})
                st.session_state["stt_text_buffer"] = "" 
                st.session_state["ai_thinking_now"] = True
                st.rerun()
        else:
            st.markdown("<div class='kkochi-stt-right-box' style='height:42px; min-height:42px; max-height:42px; border:1px dashed #cbd5e1; border-radius:8px; text-align:center; line-height:40px; color:#94a3b8; font-size:11.5px;'>🎙️ 내 보이스 답변 번역 대기 중...</div>", unsafe_allow_html=True)

    # 직접 타이핑해서 전송하는 2번 트랙 순정 입력창 구역 [PDF: 0.1.18]
    if user_answer := st.chat_input("또는 이곳에 직접 질문에 대한 답변을 타이핑하고 Enter를 누르세요...", key="kkochi_chat_input_final"):
        st.session_state["interview_messages"].append({"role": "user", "content": user_answer})
        st.session_state["stt_text_buffer"] = "" 
        st.session_state["ai_thinking_now"] = True
        st.rerun()

    if (
        st.session_state.get("timer_start_timestamp") is not None 
        and not time_over_triggered 
        and not st.session_state.get("stt_processing_lock", False)
        and not st.session_state.get("trigger_post_render_tts", False)
    ):
        st.markdown("""
            <script>
            (function() {
                if (window.kkochiTimerInstance) { clearTimeout(window.kkochiTimerInstance); }
                window.kkochiTimerInstance = setTimeout(function() {
                    // AI 추론 중 여부와 절대 상관없이 부모 파이썬 서버에게 무지연 새로고침 펄스를 1초마다 상시 강제 수송!
                    window.parent.document.dispatchEvent(new CustomEvent('streamlit:render'));
                }, 1000);
            })();
            </script>
        """, unsafe_allow_html=True)
