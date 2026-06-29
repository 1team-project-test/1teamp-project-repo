import streamlit as st
import json
import mariadb_control as db

def render_history_page():
    """🎯 나의 과거 면접 기록 관리 화면 (선택 시 100% 와이드 스위칭 및 다른 이력 보기 버튼 구현판)"""
    uid = st.session_state["user_info"]["user_id"]

    # 💡 [하이엔드 컴팩트 카드 CSS] 3색 입체 리포트 카드가 보드판에 꽉 차서 쾌적하게 보이도록 정밀 마감
    st.markdown("""
        <style>
        div.kkochi-dashboard-panel { margin-top: 147px !important; }
        div[data-baseweb="radio"] label { font-size: 13px !important; color: #4a5568 !important; padding: 4px 0; }
        
        /* 채팅 말풍선 수직 도킹 무드 보존 */
        div[data-testid='stChatMessage'] { background-color: transparent !important; padding: 4px 0 !important; margin-bottom: 2px !important; }
        div[data-testid='stChatMessage'] > div:nth-child(2) { border-radius: 12px !important; padding: 10px 14px !important; font-size: 13px !important; line-height: 1.4 !important; max-width: 85% !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by assistant']) > div:nth-child(2) { background-color: #ffffff !important; border: 1px solid #eef2f6 !important; color: #1a202c !important; border-top-left-radius: 2px !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by user']) { flex-direction: row-reverse !important; text-align: left !important; }
        div[data-testid='stChatMessage']:has(div[aria-label='Chat message by user']) > div:nth-child(2) { background-color: #ff5232 !important; color: #ffffff !important; border-top-right-radius: 2px !important; margin-right: 10px !important; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }
        
        /* 📌 3색 와이드 입체 카드 테마 패널 서식 */
        .kkochi-card-wrapper { border-radius: 12px !important; padding: 14px 18px !important; margin-bottom: 12px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.01) !important; border: 1px solid transparent !important; }
        .kkochi-card-strengths { background-color: #f3faf4 !important; border-color: #d1ebd3 !important; }
        .kkochi-card-weaknesses { background-color: #fff8f5 !important; border-color: #fbe3db !important; }
        .kkochi-card-guide { background-color: #f4f9ff !important; border-color: #d6e8ff !important; }
        
        .kkochi-card-title { font-size: 14px !important; font-weight: 850 !important; margin-bottom: 6px !important; display: flex; align-items: center; gap: 6px; }
        .kkochi-card-title-strengths { color: #1e5220 !important; }
        .kkochi-card-title-weaknesses { color: #8a361e !important; }
        .kkochi-card-title-guide { color: #1e457e !important; }
        .kkochi-card-body { font-size: 13px !important; line-height: 1.55 !important; color: #333333 !important; margin: 0 !important; padding-left: 2px !important; }
        
        /* 다른 이력 보러가기 버튼 커스텀 */
        div.stButton > button[key='btn_back_to_list'] { background-color: #ffffff !important; color: #ff5232 !important; border: 1px solid #cbd5e1 !important; font-weight: 700 !important; height: 35px !important; border-radius: 6px !important; font-size: 12.5px !important; margin-bottom: 10px !important; }
        div.stButton > button[key='btn_back_to_list']:hover { background-color: #fffaf8 !important; border-color: #ff5232 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 💡 [화면 전환 통제 제어 상태 정의] 유저가 이력을 찍었는지 감지하는 세션 상태 초기화
    if "selected_history_item" not in st.session_state:
        st.session_state["selected_history_item"] = None

    histories = db.get_user_interview_histories(uid)
    if not histories:
        st.info("📂 아직 완료된 면접 이력 기록이 존재하지 않습니다. AI 실전 면접을 먼저 진행해 주세요!")
        return

    # 💡 [스위칭 로직 분기 A단계]: 아직 아무것도 체크하지 않았을 때는 보드판 전체를 "면접 보관함 목록"이 꽉 채워서 시원하게 출력!
    if st.session_state["selected_history_item"] is None:
        st.markdown("<h5 style='margin-bottom:2px;'>📁 면접 보관함 목록</h5>", unsafe_allow_html=True)
        st.caption("다시 읽어보고 싶은 시간대별 면접 이력을 선택해 주세요.")
        
        # 보드판 높이 430px 전체를 할당하여 목록이 절대 잘리지 않고 시원하게 노출되도록 배치!
        list_scroller = st.container(height=410)
        with list_scroller:
            options_map = {}
            display_list = [" 선택을 대기 중입니다..."]
            
            for h in histories:
                label = "📌 [{}] {} - {}".format(h["created_at"].strftime("%Y-%m-%d %H:%M"), h["company"], h["job"])
                options_map[label] = h
                display_list.append(label)
                
            selected_label = st.radio("이력목록", display_list, index=0, label_visibility="collapsed")
            
            # 유저가 기본 문구 외에 진짜 이력을 선택하는 순간 세션에 정보를 적재하고 리런!
            if selected_label != " 선택을 대기 중입니다...":
                st.session_state["selected_history_item"] = options_map[selected_label]
                st.rerun()

    # 💡 [스위칭 로직 분기 B단계]: 유저가 시간 이력을 체크하는 순간, 목록을 숨기고 하얀 보드판 전체를 100% 꽉 채운 와이드 리포트 모드로 변신!
    else:
        selected_h = st.session_state["selected_history_item"]
        interviewer_style = selected_h.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)")
        if not interviewer_style or str(interviewer_style).strip() == "":
            interviewer_style = "🔥 압박형 (날카로운 꼬리 질문)"

        # 📌 [유저 기획 완벽 실현] 다른 히스토리로 언제든 되돌아갈 수 있게 만드는 하이패스 백 버튼 배치!
        if st.button("◀ 다른 면접 이력 보러가기 (시간 목록 복귀)", use_container_width=True, key="btn_back_to_list"):
            st.session_state["selected_history_item"] = None
            st.rerun()

        st.markdown(
            f"<div style='background-color:#fff5f3; border-left:4px solid #ff5232; padding:6px 12px; border-radius:6px; margin-bottom:12px; font-size:12px; color:#2d3748;'> "
            f"🧠 <b>선택한 복원 세션 정보:</b> {selected_h['company']} - {selected_h['job']} &nbsp;|&nbsp; 🎯 <b>당시 면접관 성향:</b> {interviewer_style}"
            f"</div>", unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs(["💬 당시대화록 복원 (와이드 뷰)", "📊 당시 AI 피드백 복원 (와이드 뷰)"])
        
        with tab1:
            # 보드판 내부를 꽉 채워 텍스트 줄 바꿈 밀림 없는 쾌적한 챗창 구현
            chat_scroller = st.container(height=340)
            with chat_scroller:
                try:
                    chat_log_raw = selected_h.get("chat_log", "[]")
                    logs = json.loads(chat_log_raw) if chat_log_raw else []
                    for msg in logs:
                        with st.chat_message(msg["role"]): st.write(msg["content"])
                except:
                    st.error("⚠️ 대화 기록 데이터 파싱에 실패했습니다.")
                    
        with tab2:
            # 3색 평가서 리포트가 찢어짐 없이 광활하게 전개되는 스케일 업 구역!
            feedback_scroller = st.container(height=340)
            with feedback_scroller:
                f_log = selected_h.get("feedback_log", "")
                if f_log and f_log.strip() != "":
                    try:
                        f_data = json.loads(f_log)
                        score = f_data.get('total_score', 85)
                        grade = f_data.get('grade', 'A')
                        
                        st.markdown(
                            f"<div style='display:flex; align-items:center; gap:8px; background-color:#fffdfa; border:1px solid #fde8bf; border-radius:10px; padding:10px 16px; margin-bottom:14px; box-shadow:0 4px 10px rgba(0,0,0,0.01);'>"
                            f"  <span style='font-size:15px; font-weight:900; color:#2d3748;'>🍢 종합 면접 채점 결과 리포트:</span>"
                            f"  <span style='font-size:19px; font-weight:950; color:#ff5232; margin-left:4px;'>{score}점</span>"
                            f"  <span style='background-color:#e2f7e3; color:#1e5220; font-size:11px; font-weight:800; padding:3px 8px; border-radius:20px; margin-left:auto;'>등급: {grade}</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                        
                        st.markdown(
                            f"<div class='kkochi-card-wrapper kkochi-card-strengths'>"
                            f"  <div class='kkochi-card-title kkochi-card-title-strengths'>👍 당시 나의 장점 핵심 요약</div>"
                            f"  <p class='kkochi-card-body'>{f_data.get('strengths', '내용 없음')}</p>"
                            f"</div>", unsafe_allow_html=True
                        )
                        
                        st.markdown(
                            f"<div class='kkochi-card-wrapper kkochi-card-weaknesses'>"
                            f"  <div class='kkochi-card-title kkochi-card-title-weaknesses'>⚠️ 당시 아쉬운 보완점 분석</div>"
                            f"  <p class='kkochi-card-body'>{f_data.get('weaknesses', '내용 없음')}</p>"
                            f"</div>", unsafe_allow_html=True
                        )
                        
                        st.markdown(
                            f"<div class='kkochi-card-wrapper kkochi-card-guide'>"
                            f"  <div class='kkochi-card-title kkochi-card-title-guide'>💡 AI 추천 모범 답안 가이드</div>"
                            f"  <p class='kkochi-card-body'>{f_data.get('best_answer_guide', '내용 없음')}</p>"
                            f"</div>", unsafe_allow_html=True
                        )
                    except:
                        st.info("📋 파싱되지 않은 리포트 원문:\n\n" + f_log)
                else:
                    st.warning("⚠️ 해당 면접 세션은 중간에 종료되어 AI 채점 리포트가 존재하지 않습니다.")
