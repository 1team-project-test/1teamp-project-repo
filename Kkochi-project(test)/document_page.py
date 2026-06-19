import streamlit as st
import re
import os
import json
import requests
import mariadb_control as db
from docx import Document
import io

def parse_document_via_ai(text_content):
    """🤖 [온프레미스] Ollama 최적화 generate 엔드포인트 연동으로 'message' 에러 완벽 해결"""
    try:
        # 💡 [핵심 교정] 호환성이 가장 확실하고 간결한 기본 텍스트 생성 API 주소(generate)로 전환
        url = "http://localhost:11434/api/generate"
        
        # 구글 gemma2:9b가 이해하기 쉽게 정밀 프롬프트 결합
        final_prompt = (
            "너는 이력서와 자기소개서 전문 파서 엔진이다. 제공된 텍스트를 철저히 분석해서 반드시 다음 4개의 키를 가진 JSON 오브젝트로만 응답해라. "
            "JSON 마크다운 기호(```json)나 다른 설명 텍스트는 절대 붙이지 말고 순수 JSON 문자열만 출력해라.\n\n"
            "[필수 반환 JSON 키 규칙]\n"
            "- 'skills_and_specs': 보유 기술, 학력, 자격증 스펙 요약 문장\n"
            "- 'experience_projects': 경력 사항 및 수행 프로젝트 이력 요약 문장\n"
            "- 'motivation': 지원 동기 및 입사 후 포부 요약 문장\n"
            "- 'personality': 성격의 장단점 및 가치관 요약 문장\n\n"
            "[지원자 서류 본문 데이터]\n"
            "{}"
        ).format(text_content)

        payload = {
            "model": "gemma2:9b", # 💡 사용자가 성공한 구글 gemma2:9b 모델 고정 반영
            "prompt": final_prompt.strip(),
            "options": {"temperature": 0.0},
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=60)
        res_json = response.json()
        
        # 💡 [오류 해결 핵심] /api/generate 주소의 정식 리턴 키인 'response'에서 안전하게 텍스트 추출!
        if "response" in res_json:
            content_text = res_json["response"].strip()
            return json.loads(content_text)
        return {"skills_and_specs": "", "experience_projects": "", "motivation": "", "personality": ""}
    except Exception as e:
        print("[Local AI Parser Error] 상세 원인: {}".format(e))
        return {"skills_and_specs": "", "experience_projects": "", "motivation": "", "personality": ""}

def extract_text_from_docx(uploaded_file):
    """업로드된 바이너리 .docx 파일에서 순수 한글 텍스트 본문 전체를 긁어오는 유틸 함수"""
    try:
        doc = Document(io.BytesIO(uploaded_file.read()))
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        return "[Word 파싱 실패]: {}".format(e)

def render_document_page():
    """📄 이력서 및 자기소개서 분리 제출 및 자동 AI 파싱 연동 화면"""
    if not st.session_state.get("db_data_fetched") and st.session_state.get("logged_in"):
        user_info = st.session_state.get("user_info")
        if not user_info:
            return  # 💡 로그인 정보가 잠시 비어있으면 에러 없이 조용히 대기합니다.
        uid = user_info.get("user_id")
        saved_data = db.get_user_resume(uid)
        if saved_data:
            st.session_state["selected_company"] = saved_data.get("company", "")
            st.session_state["selected_job"] = saved_data.get("job", "")
            st.session_state["interviewer_style"] = saved_data.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)")
            st.session_state["document_text"] = saved_data.get("full_text", "")
            st.session_state["document_loaded"] = True
            st.session_state["db_data_fetched"] = True
            
            raw_full = saved_data.get("full_text", "")
            if "[자기소개서 내용]" in raw_full:
                parts = raw_full.split("[자기소개서 내용]")
                st.session_state["resume_text"] = parts[0].replace("[이력서 내용]\n", "").strip()
                st.session_state["intro_text"] = parts[1].strip()
            else:
                st.session_state["resume_text"] = raw_full
                st.session_state["intro_text"] = ""

    st.subheader("📄 서류 제출 및 AI 자동 파싱 세팅")
    st.caption("사내 인프라의 구글 Gemma2 모델이 이력서와 자소서 문맥을 완벽한 대외비 보안 상태로 자동 분할합니다.")
    st.markdown("---")

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("##### 🎯 면접 목표 지정")
        company = st.text_input("지원 기업명", value=st.session_state.get("selected_company", ""), placeholder="예: 꼬치전자, 네이버")
        
        # 💡 AI-Hub 실제 폴더명과 100% 일치시킨 7가지 직무 리스트
        job_options = [
            "Management", 
            "SalesMarketing", 
            "PublicService", 
            "RND", 
            "ICT", 
            "Design", 
            "ProductionManufacturing"
        ]
        
        current_job = st.session_state.get("selected_job", job_options[0])
        default_job_index = job_options.index(current_job) if current_job in job_options else 0
        
        # 깔끔하게 한 줄로 정리되는 드롭다운 형식
        job = st.selectbox("지원 직무", job_options, index=default_job_index)
        
        st.write("")
        st.markdown("##### 🤖 AI 면접관 성향 선택")
        styles_list = ["🔥 압박형 (날카로운 꼬리 질문)", "🤝 공감형 (부드러운 칭찬 중심)", "📊 원칙형 (논리적 팩트 체크)"]
        current_style = st.session_state.get("interviewer_style", "🔥 압박형 (날카로운 꼬리 질문)")
        default_index = styles_list.index(current_style) if current_style in styles_list else 0
        interviewer_style = st.radio("면접관의 스타일을 지정하세요", styles_list, index=default_index)

    with col2:
        st.markdown("##### 📁 서류 파일 업로드 (선택 가능)")
        file_col1, file_col2 = st.columns(2, gap="medium")
        resume_text, intro_text = "", ""
        
        with file_col1:
            st.markdown("<small>**1️⃣ 이력서 파일**</small>", unsafe_allow_html=True)
            up_resume = st.file_uploader("여기에 드래그하거나 클릭", type=["txt", "pdf", "docx"], key="uploader_resume", label_visibility="collapsed")
            if up_resume is not None:
                resume_text = extract_text_from_docx(up_resume) if up_resume.name.endswith(".docx") else up_resume.read().decode("utf-8")
                st.success("✔️ 이력서 등록 완료")

        with file_col2:
            st.markdown("<small>**2️⃣ 자기소개서 파일**</small>", unsafe_allow_html=True)
            up_intro = st.file_uploader("여기에 드래그하거나 클릭", type=["txt", "pdf", "docx"], key="uploader_intro", label_visibility="collapsed")
            if up_intro is not None:
                intro_text = extract_text_from_docx(up_intro) if up_intro.name.endswith(".docx") else up_intro.read().decode("utf-8")
                st.success("✔️ 자기소개서 등록 완료")

        if not up_resume and not up_intro and st.session_state.get("document_loaded"):
            st.success("📂 MariaDB에 저장되어 있던 기존 서류 데이터 복원 연동 완료!")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("💾 설정 및 서류 저장", use_container_width=True, type="primary", key="btn_save_document"):
            final_resume = resume_text if resume_text else st.session_state.get("resume_text", "")
            final_intro = intro_text if intro_text else st.session_state.get("intro_text", "")
            
            if company.strip() and job.strip() and (final_resume.strip() or final_intro.strip()):
                combined_raw_text = "[이력서 내용]\n{}\n\n[자기소개서 내용]\n{}".format(final_resume, final_intro).strip()
                
                with st.spinner("🤖 사내 로컬 AI가 이력서/자소서 핵심 문맥을 대외비 분석 중입니다..."):
                    parsed_json = parse_document_via_ai(combined_raw_text)
                
                st.session_state.update({
                    "selected_company": company, "selected_job": job, "interviewer_style": interviewer_style,
                    "resume_text": final_resume, "intro_text": final_intro, "document_text": combined_raw_text, "document_loaded": True
                })
                
                user_info = st.session_state.get("user_info")
                uid = user_info.get("user_id") if user_info else "unknown"
                db_success = db.save_parsed_resume(
                    user_id=uid, company=company, job=job, style=interviewer_style, file_name=up_resume.name if up_resume else "통합제출",
                    skills=parsed_json.get("skills_and_specs", ""), exp=parsed_json.get("experience_projects", ""),
                    motiv=parsed_json.get("motivation", ""), personality=parsed_json.get("personality", ""), raw_text=combined_raw_text
                )
                if db_success: st.success("🎉 사내 서버 AI 자동 파싱 및 MariaDB 영구 적재 완료!")
                else: st.error("⚠️ 파싱은 완료되었으나 DB 트랜잭션 통신 중 오류가 발생했습니다.")
            else:
                st.warning("⚠️ 기업명, 직무를 입력하고 서류 파일을 1개 이상 첨부해 주세요.")
                
    with btn_col2:
        if st.session_state.get("document_loaded"):
            if st.button("🤖 AI 실전 면접방으로 즉시 이동하기 ➡️", use_container_width=True, key="btn_go_to_interview"):
                st.session_state.pop("interview_messages", None)
                st.session_state["current_menu"] = "🤖 실전 면접방"
                st.rerun()