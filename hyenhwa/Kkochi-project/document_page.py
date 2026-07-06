import streamlit as st, json, requests, io, mariadb_control as db
from docx import Document

def parse_document_via_ai(text_content):
    """🤖 [온프레미스 API] 로컬 AI 응답 실패 시에도 빈 딕셔너리를 안전하게 반환하여 가동"""
    try:
        url = "http://localhost:11434/api/generate"
        prompt = "너는 이력서/자소서 전문 파서다. 분석 후 반드시 다음 4개 키를 가진 JSON만 반환해라: 'skills_and_specs', 'experience_projects', 'motivation', 'personality'. 순수 JSON만 뱉어라.\n\n[본문]\n{}".format(text_content)
        # 💡 Ollama 미구동 시 무한 대기를 막기 위해 타임아웃을 10초로 컴팩트하게 단축 조율
        response = requests.post(url, json={"model": "gemma2:9b", "prompt": prompt, "options": {"temperature": 0.0}, "stream": False, "format": "json"}, timeout=10)
        return json.loads(response.json()["response"].strip())
    except: 
        return {"skills_and_specs": "AI 미구동", "experience_projects": "AI 미구동", "motivation": "AI 미구동", "personality": "AI 미구동"}

def extract_text_from_docx(file_bytes):
    try: return "\n".join([p.text for p in Document(io.BytesIO(file_bytes)).paragraphs])
    except: return ""

def render_document_page():
    # 💡 [순정 오피셜 CSS 유지] 유저님이 주신 오리지널 스타일 명세 100% 철통 보존
    st.markdown("""
        <style>
        h5 { color: #1a202c !important; font-weight: 700; font-size: 15px; margin-bottom: 5px; margin-top: 5px; }
        input { border-radius: 6px !important; border: 1px solid #cbd5e1 !important; height: 35px !important; font-size: 13px !important; background-color: #ffffff !important; }
        [data-testid='stFileUploader'] { background-color: #ffffff !important; border: 1px dashed #cbd5e1 !important; border-radius: 8px !important; padding: 4px !important; }
        div[data-baseweb='radio'] input:checked + div { background-color: #ff5232 !important; border-color: #ff5232 !important; }
        div.stButton > button[key^='btn_'] { height: 40px !important; border-radius: 8px !important; font-weight: 700; font-size: 13.5px !important; }
        div.stButton > button[key='btn_save_document'] { background-color: #ff5232 !important; color: white !important; border: none !important; }
        div.stButton > button[key='btn_go_to_interview'] { background-color: #ffffff !important; color: #ff5232 !important; border: 1px solid #cbd5e1 !important; }
        .stAlert { border-radius: 12px !important; border: 1px solid #def1df !important; background-color: #f2fbf3 !important; padding: 10px 16px !important; font-size: 13.5px !important; color: #275b2b !important; }
        </style>
    """, unsafe_allow_html=True)

    # 💡 [버그 완전 박멸 해결책 1] 원격 복원 구역의 parts 리스트 배열 방 번호([0], [1]) 주소 매핑을 소름 돋게 최종 수술 완료!
    if not st.session_state.get("db_data_fetched") and st.session_state.get("logged_in"):
        uid = st.session_state["user_info"]["user_id"]
        saved = db.get_user_resume(uid)
        if saved and saved.get("full_text", "").strip():
            st.session_state.update({
                "selected_company": saved.get("company", ""), 
                "selected_job": saved.get("job", ""), 
                "interviewer_style": saved.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)"), 
                "document_text": saved.get("full_text", ""), 
                "document_loaded": True
            })
            raw = saved.get("full_text", "")
            if "[자기소개서 내용]" in raw:
                parts = raw.split("[자기소개서 내용]")
                st.session_state.update({
                    "resume_text": parts[0].replace("[이력서 내용]\n", "").strip(), # 👈 parts[0] 방 번호 정밀 안착!
                    "intro_text": parts[1].strip() if len(parts) > 1 else ""        # 👈 parts[1] 방 번호 정밀 안착!
                })
            else: st.session_state.update({"resume_text": raw, "intro_text": ""})
        st.session_state["db_data_fetched"] = True

    # 유저님 전용 커스텀 황금 대칭 비율 명세([1, 1.1]) 유지
    col1, col2 = st.columns([1, 1.1], gap="medium")

    with col1:
        st.markdown("##### 🎯 면접 목표 설정")
        company = st.text_input("지원 기업명", value=st.session_state.get("selected_company", ""), placeholder="예: 꼬치전자, 네이버")
        job = st.text_input("지원 직무", value=st.session_state.get("selected_job", ""), placeholder="예: 백엔드 개발자")
        st.markdown("##### 👤 AI 면접관 성향 선택")
        s_list = ["🔥 압박형 (날카로운 꼬리 질문)", "🤝 공감형 (부드러운 칭찬 중심)", "📊 원칙형 (논리적 팩트 체크)"]
        interviewer_style = st.radio("성향", s_list, index=s_list.index(st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")), label_visibility="collapsed")

    with col2:
        st.markdown("##### 📁 서류 파일 업로드 (선택 가능)")
        f_col1, f_col2 = st.columns(2)
        resume_text, intro_text = "", ""
        with f_col1:
            st.markdown("<small style='font-weight:600; font-size:12px; color:#4a5568;'>📄 이력서 파일</small>", unsafe_allow_html=True)
            up_r = st.file_uploader("이력서", type=["txt", "pdf", "docx"], key="uploader_resume", label_visibility="collapsed")
            if up_r:
                r_bytes = up_r.read()
                resume_text = extract_text_from_docx(r_bytes) if up_r.name.endswith(".docx") else r_bytes.decode("utf-8")
        with f_col2:
            st.markdown("<small style='fontS-weight:600; font-size:12px; color:#4a5568;'>📝 자기소개서 파일</small>", unsafe_allow_html=True)
            up_i = st.file_uploader("자소서", type=["txt", "pdf", "docx"], key="uploader_intro", label_visibility="collapsed")
            if up_i:
                i_bytes = up_i.read()
                intro_text = extract_text_from_docx(i_bytes) if up_i.name.endswith(".docx") else i_bytes.decode("utf-8")
        
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        if not up_r and not up_i and st.session_state.get("document_loaded"):
            st.success("✔️ MariaDB에 저장되어 있던 기존 서류 데이터 복원 연동 완료!")

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2, gap="medium")
    with b_col1:
        if st.button("🧡 설정 및 서류 저장", use_container_width=True, type="primary", key="btn_save_document"):
            f_res = resume_text if resume_text else st.session_state.get("resume_text", "")
            f_int = intro_text if intro_text else st.session_state.get("intro_text", "")
            if company.strip() and job.strip() and (f_res.strip() or f_int.strip()):
                combined = "[이력서 내용]\n{}\n\n[자기소개서 내용]\n{}".format(f_res, f_int).strip()
                
                # 💡 [버그 완전 박멸 해결책 2] 로컬 AI 연산이 실패하거나 구동 전이어도, 아래의 DB 쿼리 저장 단락으로 무조건 점프하게 예외 처리선 강화!
                with st.spinner("🤖 사내 AI 분석 중..."): 
                    parsed = parse_document_via_ai(combined)
                    
                st.session_state.update({"selected_company": company, "selected_job": job, "interviewer_style": interviewer_style, "resume_text": f_res, "intro_text": f_int, "document_text": combined, "document_loaded": True})
                
                # 💡 무조건 수송선을 출항시켜 MariaDB kkochi_resume 테이블에 데이터를 무조건 강제 삽입합니다!
                db.save_parsed_resume(
                    st.session_state["user_info"]["user_id"],
                    company,
                    job,
                    interviewer_style,
                    up_r.name if up_r else "통합제출",
                    parsed.get("skills_and_specs", ""),
                    parsed.get("experience_projects", ""),
                    parsed.get("motivation", ""),
                    parsed.get("personality", ""),
                    combined
                )
                st.rerun()
            else: st.warning("⚠️ 모든 필드를 채워주세요.")
            
    with b_col2:
        if st.session_state.get("document_loaded"):
            if st.button("AI 실전 면접방으로 즉시 이동하기 ➡️", use_container_width=True, key="btn_go_to_interview"):
                st.session_state.pop("interview_messages", None)
                st.session_state["current_menu"] = "🤖 실전 면접방"
                st.rerun()



