import streamlit as st
import re
import os
import json
import mariadb_control as db
from openai import OpenAI
from docx import Document
import io

def parse_document_via_ai(text_content):
    """OpenAI API를 활용해 한글 서류 문맥을 완벽 분석하고 4대 항목 JSON으로 자동 파싱"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "너는 이력서와 자기소개서 전문 파서 엔진이다. 제공된 텍스트를 철저히 분석해서 반드시 다음 4개의 키를 가진 JSON 오브젝트로만 응답해라: 'skills_and_specs' (보유 기술, 학력, 자격증 스펙), 'experience_projects' (경력 사항 및 수행 프로젝트 이력), 'motivation' (지원 동기 및 입사 후 포부), 'personality' (성격의 장단점 및 가치관). 텍스트에서 해당하는 내용이 있다면 핵심 요약 문장으로 채우고, 전혀 없다면 빈 문자열로 채워라."},
                {"role": "user", "content": text_content}
            ],
            temperature=0.0
        )
        return json.loads(response.choices.message.content)
    except:
        return {"skills_and_specs": "", "experience_projects": "", "motivation": "", "personality": ""}

def extract_text_from_docx(uploaded_file):
    """업로드된 바이너리 .docx 파일에서 순수 한글 텍스트 본문 전체를 긁어오는 유틸 함수"""
    try:
        doc = Document(io.BytesIO(uploaded_file.read()))
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        return f"[Word 파싱 실패]: {e}"

def render_document_page():
    """📄 이력서 및 자기소개서 분리 제출 및 자동 AI 파싱 연동 화면 (DB 자동 불러오기 내장)"""
    
    # 💡 [신규 추가] 세션에 불러오기 실행 기록이 없고 로그인된 상태라면, MariaDB에서 기존 데이터 원격 로드
    if not st.session_state.get("db_data_fetched") and st.session_state.get("logged_in"):
        uid = st.session_state["user_info"]["user_id"]
        saved_data = db.get_user_resume(uid)
        
        if saved_data:
            # 기존 저장값이 존재하면 세션 메모리에 선제 적재하여 필드 초기값으로 밀어줌
            st.session_state["selected_company"] = saved_data.get("company", "")
            st.session_state["selected_job"] = saved_data.get("job", "")
            st.session_state["interviewer_style"] = saved_data.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)")
            st.session_state["document_text"] = saved_data.get("full_text", "")
            st.session_state["document_loaded"] = True
            
            # 파싱 완료된 원문 텍스트 속에서 이력서와 자소서를 구별해 세션 분할 복원
            raw_full = saved_data.get("full_text", "")
            if "[자기소개서 내용]" in raw_full:
                parts = raw_full.split("[자기소개서 내용]")
                st.session_state["resume_text"] = parts[0].replace("[이력서 내용]\n", "").strip()
                st.session_state["intro_text"] = parts[1].strip()
            else:
                st.session_state["resume_text"] = raw_full
                st.session_state["intro_text"] = ""
                
        # 중복 트랜잭션 방지를 위해 불러오기 완료 플래그 고정
        st.session_state["db_data_fetched"] = True

    st.subheader("📄 서류 제출 및 AI 자동 파싱 세팅")
    st.caption("업로드하신 서류 문맥을 AI가 자동으로 파싱하여 MariaDB 데이터베이스에 구조화하여 저장합니다.")
    st.markdown("---")

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("##### 🎯 면접 목표 지정")
        company = st.text_input("지원 기업명", value=st.session_state.get("selected_company", ""), placeholder="예: 꼬치전자, 네이버")
        job = st.text_input("지원 직무", value=st.session_state.get("selected_job", ""), placeholder="예: 백엔드 개발자")
        
        st.write("")
        st.markdown("##### 🤖 AI 면접관 성향 선택")
        
        # 💡 라디오 버튼 인덱스 복원 매핑 배열 생성
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

        # 💡 [UI 보완] DB에서 기존 서류를 정상 복원해 왔을 때 시각적 피드백 제공 가이드 추가
        if not up_resume and not up_intro and st.session_state.get("document_loaded"):
            st.success("📂 MariaDB에 저장되어 있던 기존 서류 데이터 복원 연동 완료!")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("💾 설정 및 서류 저장", use_container_width=True, type="primary", key="btn_save_document"):
            final_resume = resume_text if resume_text else st.session_state.get("resume_text", "")
            final_intro = intro_text if intro_text else st.session_state.get("intro_text", "")
            
            if company.strip() and job.strip() and (final_resume.strip() or final_intro.strip()):
                combined_raw_text = f"[이력서 내용]\n{final_resume}\n\n[자기소개서 내용]\n{final_intro}".strip()
                
                with st.spinner("🤖 AI가 이력서/자소서 핵심 문맥을 분석하여 파싱하는 중입니다..."):
                    parsed_json = parse_document_via_ai(combined_raw_text)
                
                st.session_state.update({
                    "selected_company": company, "selected_job": job, "interviewer_style": interviewer_style,
                    "resume_text": final_resume, "intro_text": final_intro, "document_text": combined_raw_text, "document_loaded": True
                })
                
                uid = st.session_state["user_info"]["user_id"]
                db_success = db.save_parsed_resume(
                    user_id=uid, company=company, job=job, style=interviewer_style, file_name=up_resume.name if up_resume else "통합제출",
                    skills=parsed_json.get("skills_and_specs", ""), exp=parsed_json.get("experience_projects", ""),
                    motiv=parsed_json.get("motivation", ""), personality=parsed_json.get("personality", ""), raw_text=combined_raw_text
                )
                
                if db_success: st.success("🎉 AI 자동 파싱 및 MariaDB 테이블 영구 적재가 완벽히 완료되었습니다!")
                else: st.error("⚠️ 파싱은 완료되었으나 DB 트랜잭션 통신 중 오류가 발생했습니다.")
            else:
                st.warning("⚠️ 기업명, 직무를 입력하고 서류 파일을 1개 이상 첨부해 주세요.")
                
    with btn_col2:
        if st.session_state.get("document_loaded"):
            if st.button("🤖 AI 실전 면접방으로 즉시 이동하기 ➡️", use_container_width=True, key="btn_go_to_interview"):
                st.session_state.pop("interview_messages", None)
                st.session_state["current_menu"] = "🤖 실전 면접방"
                st.rerun()