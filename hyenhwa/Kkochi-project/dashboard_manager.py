import os
import base64
import streamlit as st
import document_page
import interview_page
import feedback_page
import history_page

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 💡 [에러 완치 핵심 핀포인트] main.py가 부르는 이름과 토씨 하나 틀리지 않게 'render_dashboard_layout'으로 고정!
def render_dashboard_layout():
    """🍢 [대시보드 총괄 매니저] 유저님 커스텀 수치[0.9, 3.1] 및 예전 순정 무드를 100% 유지하는 마감판"""
    
    bg_img = "background2.png"
    bg_url = f"data:image/png;base64,{get_base64_image(bg_img)}" if os.path.exists(bg_img) else ""
    cur_m = st.session_state.get("current_menu", "📄 이력서 제출")
    
    st.markdown(f"""
        <style>
        [data-testid='stAppViewContainer'] {{
            background: url('{bg_url}') no-repeat center center / contain !important;
            background-color: #f5eae1 !important;
            background-attachment: fixed !important;
            overflow: hidden !important; 
        }}
        .main, .block-container {{
            background-color: transparent !important;
            padding: 0 !important;
            margin-top: 250px !important;
            width: 1150px !important;
            max-width: 1150px !important;
            height: 670px !important;
            position: relative !important;
            overflow: hidden !important; 
        }}
        [data-testid='stHeader'], [data-testid='stSidebar'], [data-testid='stSidebarCollapseButton'] {{
            display: none !important;
        }}
        
        /* 📌 1. 좌측 글자 및 메뉴 버튼 더미 위치 제어 (유저님이 수치를 고칠 수 있도록 개정된 복합 체인 유지) */
        div.kkochi-profile-panel,
        div.kkochi-profile-panel ~ div,
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stBlock"] {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            
            /* 💡 [위치 조율 가이드] 유저님이 원하는 글씨와 메뉴 높이에 맞게 이 숫자를 미세하게 매만지시면 됩니다! */
            margin-top: 242px !important;  
            
            width: 122px !important;         
            position: absolute !important;
            left: 175px !important;          
            z-index: 9999 !important;
        }}
        
        .kkochi-user-name {{ font-size: 16.5px !important; font-weight: 800 !important; color: #2d3748 !important; margin-bottom: 4px; text-align: left !important; padding-left: 14px !important; }}
        .kkochi-user-sub {{ font-size: 10.5px !important; color: #718096 !important; margin-bottom: 20px; text-align: left !important; padding-left: 14px !important; white-space: nowrap !important; }}
        
        /* 메뉴 버튼 글씨 및 패딩 간격 (유저님이 조정하고 싶어 하셨던 가로/세로 오프셋 구역) */
        div.kkochi-menu-area button {{
            background-color: transparent !important;
            border: 2px solid transparent !important;
            color: #4a5568 !important;
            font-size: 12px !important;
            height: 34px !important;
            margin-bottom: 4px !important;
            font-weight: 700 !important;
            width: 100% !important;
            text-align: left !important;
            
            /* 💡 [글씨 가로 위치 꿀팁] 이 padding-left 숫자를 키울수록 버튼 글씨들이 통째로 오른쪽으로 수평 이동합니다! */
            padding-left: 14px !important;
            
            box-shadow: none !important;
            outline: none !important;
            transition: all 0.2s ease !important;
        }}
        div.kkochi-menu-area button:hover {{ color: #ff5232 !important; background-color: rgba(255,82,50,0.02) !important; }}
        
        /* 진입 탭 메뉴 동적 하이라이트 */
        div.kkochi-menu-area div:nth-child({1 if cur_m == "📄 이력서 제출" else 2 if cur_m == "🤖 실전 면접방" else 3 if cur_m == "📊 면접 피드백" else 4}) button {{
            border: 2px solid #fde8bf !important;
            background-color: rgba(253, 232, 191, 0.2) !important;
            color: #ff5232 !important;
        }}
        
        /* 📌 2. 우측 알맹이 기능창 전용 대시보드 패널 위치 고정 보존 */
        div.kkochi-dashboard-panel {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            position: absolute !important;
            top: 165px !important;                       
            left: 310px !important;                      
            width: 660px !important;                     
            height: 480px !important;                    
            overflow-y: auto !important;                 
            padding: 10px 20px 20px 25px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # 💡 아침에 매만져놓으셨던 오리지널 [0.9, 3.1] 화면 분리형 칼럼 구조 유지
    main_col1, main_col2 = st.columns([0.9, 3.1], gap="small")

    with main_col1:
        st.markdown('<div class="kkochi-profile-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="kkochi-user-name">{st.session_state["user_info"]["username"]}님</div>', unsafe_allow_html=True)
        st.markdown('<div class="kkochi-user-sub">면접 코칭을 시작해볼까요?</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="kkochi-menu-area">', unsafe_allow_html=True)
        if st.button("📄 이력서 제출방", key="m_doc"): st.session_state["current_menu"] = "📄 이력서 제출"; st.rerun()
        if st.button("🤖 실전 면접방", key="m_int"): st.session_state["current_menu"] = "🤖 실전 면접방"; st.rerun()
        if st.button("📊 면접 피드백", key="m_feed"): st.session_state["current_menu"] = "📊 면접 피드백"; st.rerun()
        if st.button("🎯 면접 이력 관리", key="m_hist"): st.session_state["current_menu"] = "🎯 면접 이력 관리"; st.rerun()
        st.write("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 로그아웃", key="m_logout"):
            st.session_state.update({"logged_in": False, "user_info": None})
            st.query_params.clear()
            for key in ["document_loaded", "db_data_fetched", "selected_company", "selected_job", "resume_text", "intro_text", "document_text", "interview_messages", "feedback_report"]: st.session_state.pop(key, None)
            st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

    with main_col2:
        st.markdown('<div class="kkochi-dashboard-panel">', unsafe_allow_html=True)
        menu = st.session_state["current_menu"]
        if menu == "📄 이력서 제출": document_page.render_document_page()
        elif menu == "🤖 실전 면접방": interview_page.render_interview_page()
        elif menu == "📊 면접 피드백": feedback_page.render_feedback_page()
        elif menu == "🎯 면접 이력 관리": history_page.render_history_page()
        st.markdown('</div>', unsafe_allow_html=True)
