import os
import base64
import streamlit as st
from dotenv import load_dotenv
import auth
import document_page
import interview_page
import feedback_page
import history_page
import mariadb_control as db

load_dotenv()
st.set_page_config(page_title="꼬치꼬치 - AI 면접 코칭", page_icon="🍢", layout="wide")

# 💡 [핵심 교정] 주소창의 파라미터(sid)를 스캔하여 세션 복원 베이스 추적 가동
saved_user_id = st.query_params.get("sid", "")

if "logged_in" not in st.session_state:
    if saved_user_id:
        # 💡 새로고침(F5)으로 메모리가 증발했더라도, 주소창의 sid 토큰을 판정하여 MariaDB 자동 원상 복구 개시
        with db.get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(db.N))
            cur.execute("SELECT * FROM {} WHERE user_id = %s".format(db.T), (saved_user_id,))
            user_record = cur.fetchone()
            
        if user_record:
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = user_record
            
            # 사내 이력 정보 실시간 고정 복원
            saved_resume = db.get_user_resume(saved_user_id)
            if saved_resume:
                st.session_state["selected_company"] = saved_resume.get("company", "")
                st.session_state["selected_job"] = saved_resume.get("job", "")
                st.session_state["interviewer_style"] = saved_resume.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)")
                st.session_state["document_text"] = saved_resume.get("full_text", "")
                st.session_state["document_loaded"] = True
                st.session_state["db_data_fetched"] = True
        else:
            st.session_state["logged_in"] = False
    else:
        st.session_state["logged_in"] = False

# 기본 세션 초기값 정렬
for key, default in [("user_info", None), ("show_auth_page", False), ("current_menu", "📄 이력서 제출")]:
    if key not in st.session_state:
        st.session_state[key] = default

# 대문 시작하기 버튼 유도 분기 파라미터 감지
if "trigger_auth" in st.query_params:
    st.query_params.clear()
    st.session_state["show_auth_page"] = True
    st.rerun()

def get_base64_image(path):
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

# --- 미로그인 화면 분기 ---
if not st.session_state["logged_in"]:
    if st.session_state["show_auth_page"]:
        auth.render_auth_page()
    else:
        bg, btn = "bg.png", "startbutton.png"
        if os.path.exists(bg) and os.path.exists(btn):
            bg_url = f"data:image/png;base64,{get_base64_image(bg)}"
            btn_url = f"data:image/png;base64,{get_base64_image(btn)}"
            st.markdown(
                "<style>"
                "[data-testid='stHeader'] { display: none !important; }"
                ".main, .block-container, [data-testid='stAppViewContainer'] {"
                "    width: auto !important; height: auto !important; padding: 0 !important; margin: 0 !important;"
                "    overflow-x: auto !important; overflow-y: auto !important;"
                "}"
                ".kkochi-screen-container {"
                "    position: relative; width: 100vw; height: 100vh; min-width: 1200px; min-height: 700px;"
                f"    background: url('{bg_url}') no-repeat center center / cover;"
                "}"
                ".kkochi-responsive-btn {"
                "    position: absolute; top: 65% !important; left: 53.3% !important;"
                "    width: 26% !important; aspect-ratio: 500 / 250 !important; max-width: 500px !important; max-height: 250px !important;"
                "    transform: translate(-50%, -50%) !important;"
                f"    background: url('{btn_url}') no-repeat center center / contain !important;"
                "    border: none !important; cursor: pointer !important; z-index: 9999 !important;"
                "    transition: transform 0.1s ease !important;"
                "}"
                ".kkochi-responsive-btn:active { transform: translate(-50%, -50%) scale(0.97) !important; filter: brightness(0.9) !important; }"
                "</style>"
                "<div class='kkochi-screen-container'>"
                "    <a href='?trigger_auth=true' target='_self'><button class='kkochi-responsive-btn'></button></a>"
                "</div>", unsafe_allow_html=True
            )
        else: st.error("⚠️ 이미지 파일이 없습니다.")

# --- 로그인 완료 화면 분기 ---
else:
    st.markdown("<style>.main, .block-container, [data-testid='stAppViewContainer'] { background: none !important; padding: 2rem 1rem !important; overflow: auto !important; }</style>", unsafe_allow_html=True)
    st.title(f"🍢 {st.session_state['user_info']['username']}님의 면접 코칭방")
    
    menu_list = ["📄 이력서 제출", "🤖 실전 면접방", "📊 면접 피드백", "🎯 면접 이력 관리"]
    menu = st.sidebar.radio("이동할 페이지 선택", menu_list, index=menu_list.index(st.session_state["current_menu"]))
    st.session_state["current_menu"] = menu

    # 💡 [로그아웃 개조] 로그아웃을 누르면 주소창 파라미터(sid)를 즉시 증발 소멸
    if st.sidebar.button("로그아웃"):
        st.session_state.update({"logged_in": False, "user_info": None})
        
        # 💡 주소창 클리어 요청
        st.query_params.clear()
            
        for key in ["document_loaded", "db_data_fetched", "selected_company", "selected_job", "resume_text", "intro_text", "document_text", "interview_messages", "feedback_report"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.caption("⚡ 사내 온프레미스 AI 엔진이 보안망 내부에서 안전하게 작동 중입니다.")
    st.markdown("---")

    if menu == "📄 이력서 제출":
        document_page.render_document_page()
    elif menu == "🤖 실전 면접방":
        interview_page.render_interview_page()
    elif menu == "📊 면접 피드백":
        feedback_page.render_feedback_page()
    elif menu == "🎯 면접 이력 관리":
        history_page.render_history_page()