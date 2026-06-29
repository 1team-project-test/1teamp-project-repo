import os
import json
import streamlit as st
import requests

def generate_interview_feedback(history_messages):
    """🤖 [온프레미스] gemma2:9b 모델을 활용한 고해상도 상세 면접 채점 보고서 생성 (원본 보존)"""
    try:
        url = "http://localhost:11434/api/generate"
        
        conversation_log = ""
        for msg in history_messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            if msg["role"] == "assistant":
                conversation_log += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_log += "지원자: {}\n".format(msg["content"])

        final_prompt = f"""
        너는 대기업 인사팀장 출신의 베테랑 채용 전문가이자 professional 면접 코치이다. 
        제공된 면접 대화 기록을 면밀히 스캔하여 지원자의 역량을 날카롭고 세부적으로 채점하십시오.
        반드시 다음 5개의 키를 가진 JSON 오브젝트로만 응답하고, 마크다운 기호 없이 순수 JSON만 반환해라.
        [JSON 반환 스키마 및 가이드라인 - 중요]
        1. 'total_score' : 100점 만점 기준의 정수 점수.
        2. 'grade' : S, A, B, C 중 하나의 등급 문자.
        3. 'strengths' : 지원자의 답변 속에서 돋보인 논리성, 직무 전문성, 태도적 강점을 구체적인 답변 사례를 인용하여 '최소 3문장(4줄) 이상' 상세히 칭찬하십시오. 단답형이나 한 줄 평가서는 절대 금지합니다.
        4. 'weaknesses' : 면접관의 압박/꼬리 질문에 답변할 때 부족했던 부분, 논리적 모순, 혹은 정량적 성과(지표) 표현의 아쉬움을 날카롭게 짚어내고 '최소 3문장(4줄) 이상' 구체적으로 지적하십시오.
        5. 'best_answer_guide' : 향후 이 기업/직무 면접에서 무조건 합격하기 위해 답변을 어떻게 리프레이밍해야 하는지 두괄식(STAR 기법) 작성 요령을 포함하여 '최소 4문장(5줄) 이상'의 구체적인 솔루션과 모범 답변 예시 가이드를 친절한 경어체로 작성하십시오.
        [평가 대상 면접 대화록 기록]
        {conversation_log}
        """
        payload = {
            "model": "gemma2:9b",
            "prompt": final_prompt.strip(),
            "options": {
                "temperature": 0.4,
                "num_ctx": 8192,
                "repeat_penalty": 1.2
            },
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            res_json = response.json()
            if "response" in res_json:
                res_content = res_json["response"].strip()
                return json.loads(res_content)
        return None
    except Exception as e:
        print("[Local AI Feedback Error] 상세 원인: {}".format(e))
        return None

def render_feedback_page():
    """📊 AI 면접 종합 피드백 & 채점 리포트 화면 (독립 스크롤 및 3색 럭셔리 카드 전면 개혁판)"""
    
    # 💡 [피드백 가시성 총개혁 CSS] 거대 폰트 st.metric을 폭파하고, 눈에 확 꽂히는 3색 입체 성적표 리포트 명세 인젝션
    st.markdown("""
        <style>
        div.kkochi-dashboard-panel { margin-top: 147px !important; }
        
        /* 📌 순정 상자의 무뚝뚝한 검은 테두리와 여백 그림자를 투명화 청소 */
        div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }
        
        /* 📌 [가시성 완치 UI] 항목별 정돈된 3색 소프트 입체 패널 공통 서식 */
        .kkochi-result-card {
            border-radius: 12px !important;
            padding: 14px 18px !important;
            margin-bottom: 12px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.01) !important;
            border: 1px solid transparent !important;
        }
        .kkochi-rc-good { background-color: #f3faf4 !important; border-color: #d1ebd3 !important; }
        .kkochi-rc-bad { background-color: #fff8f5 !important; border-color: #fbe3db !important; }
        .kkochi-rc-solution { background-color: #f4f9ff !important; border-color: #d6e8ff !important; }
        
        .kkochi-rc-title { font-size: 14px !important; font-weight: 850 !important; margin-bottom: 6px !important; display: flex; align-items: center; gap: 6px; }
        .kkochi-rct-good { color: #1e5220 !important; }
        .kkochi-rct-bad { color: #8a361e !important; }
        .kkochi-rct-solution { color: #1e457e !important; }
        
        .kkochi-rc-body { font-size: 12.5px !important; line-height: 1.55 !important; color: #333333 !important; margin: 0 !important; padding-left: 2px !important; }
        
        /* 조작 버튼 서식 핏 조율 */
        div.stButton > button[key^='btn_fb_'] { background-color: #ffffff !important; color: #ff5232 !important; border: 1px solid #fbdad0 !important; font-weight: 700 !important; height: 35px !important; border-radius: 6px !important; font-size: 12.5px !important; }
        div.stButton > button[key='btn_fb_new'] { background-color: #ff5232 !important; color: white !important; border: none !important; }
        div.stButton > button[key^='btn_fb_']:hover { border-color: #ff5232 !important; background-color: #fffaf8 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 자리를 답답하게 가로막던 불필요한 설명글을 지워 세로 여백 추가 전개
    st.markdown("<h5 style='margin-bottom:10px;'>📊 AI 면접 채점 및 종합 피드백 리포트</h5>", unsafe_allow_html=True)

    report = st.session_state.get("feedback_report")
    if not report:
        st.warning("⚠️ 아직 분석된 면접 대화 기록이 존재하지 않습니다. 실전 면접방에서 먼저 면접을 종료해 주세요.")
        if st.button("🤖 실전 면접방으로 돌아가기", use_container_width=True, key="btn_fb_back"):
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
        return

    score = report.get("total_score", 72)
    grade = report.get("grade", "B")

    # 💡 [대개혁 정답 1] 거대한 점수판을 도려내고, 한 줄 가로선 안에 정갈하게 안착하는 미니 스코어보드 연동 완료!
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:8px; background-color:#fffdfa; border:1px solid #fde8bf; border-radius:10px; padding:10px 16px; margin-bottom:12px; box-shadow:0 4px 10px rgba(0,0,0,0.01);'>"
        f"  <span style='font-size:15px; font-weight:900; color:#2d3748;'>🍢 이번 훈련 종합 채점 결과 리포트:</span>"
        f"  <span style='font-size:19px; font-weight:950; color:#ff5232; margin-left:4px;'>{score}점</span>"
        f"  <span style='background-color:#e2f7e3; color:#1e5220; font-size:11px; font-weight:800; padding:3px 8px; border-radius:20px; margin-left:auto;'>등급: {grade}</span>"
        f"</div>", 
        unsafe_allow_html=True
    )

    # 💡 [대개혁 정답 2] 하단 잘림을 원천 차단하기 위해 리포트 본문 전체를 340px 세로 스크롤 그릇 내부로 완벽 격리 가둡니다!
    # 이제 리포트가 아무리 무겁고 길게 내려와도 입력 단추들을 밀어내지 않고 이 안에서만 부드럽게 스크롤바가 순환합니다.
    feedback_container = st.container(height=340)
    
    with feedback_container:
        # 👍 당시 나의 장점 핵심 요약 패널 (연녹색 카드)
        st.markdown(
            f"<div class='kkochi-result-card kkochi-rc-good'>"
            f"  <div class='kkochi-rc-title kkochi-rct-good'>👍 이번 면접에서 빛난 지원자의 장점</div>"
            f"  <p class='kkochi-rc-body'>{report.get('strengths', '내용 없음')}</p>"
            f"</div>", unsafe_allow_html=True
        )
        
        # ⚠️ 당시 아쉬운 보완점 분석 패널 (연주황색 카드)
        st.markdown(
            f"<div class='kkochi-result-card kkochi-rc-bad'>"
            f"  <div class='kkochi-rc-title kkochi-rct-bad'>⚠️ 개선이 시급한 아쉬운 보완점 분석</div>"
            f"  <p class='kkochi-report-body'>{report.get('weaknesses', '내용 없음')}</p>"
            f"</div>", unsafe_allow_html=True
        )
        
        # 💡 AI 추천 모범 답안 가이드 패널 (연푸른색 카드)
        st.markdown(
            f"<div class='kkochi-result-card kkochi-rc-solution'>"
            f"  <div class='kkochi-rc-title kkochi-rct-solution'>💡 다음 매칭을 위한 AI 추천 모범 가이드 라인</div>"
            f"  <p class='kkochi-report-body'>{report.get('best_answer_guide', '내용 없음')}</p>"
            f"</div>", unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:2px;'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2, gap="medium")
    with btn_col1:
        if st.button("🔄 이 서류로 면접 다시 도전하기", use_container_width=True, key="btn_fb_retry"):
            st.session_state.pop("interview_messages", None)
            st.session_state.pop("feedback_report", None)
            st.session_state["current_menu"] = "🤖 실전 면접방"
            st.rerun()
    with btn_col2:
        if st.button("📄 새로운 서류 제출하러 가기", use_container_width=True, type="primary", key="btn_fb_new"):
            for key in ["document_loaded", "db_data_fetched", "selected_company", "selected_job", "resume_text", "intro_text", "document_text", "interview_messages", "feedback_report"]:
                st.session_state.pop(key, None)
            st.session_state["current_menu"] = "📄 이력서 제출"
            st.rerun()
