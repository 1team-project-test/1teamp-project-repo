import os
import base64
import streamlit as st
from dotenv import load_dotenv
import auth
import document_page
import interview_page
import feedback_page  # 💡 [신규 추가] 피드백 페이지 모듈 임포트

load_dotenv()
st.set_page_config(page_title="꼬치꼬치 - AI 면접 코칭", page_icon="🍢", layout="wide")

# 세션 기본값 일괄 초기화
for key, default in [("logged_in", False), ("user_info", None), ("show_auth_page", False), ("current_menu", "📄 이력서 제출")]:
    if key not in st.session_state:
        st.session_state[key] = default

# Query Parameter 감지 시 즉시 리프레시
if "trigger_auth" in st.query_params:
    st.query_params.clear()
    st.session_state["show_auth_page"] = True
    st.rerun()

def get_base64_image(path):
    with open(path, "rb") as f: 
        return base64.b64encode(f.read()).decode()

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
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("⚠️ 배경 이미지(bg.png) 또는 버튼 이미지(startbutton.png)가 파일 경로에 없습니다.")

# --- 로그인 완료 화면 분기 ---
else:
    st.markdown("<style>.main, .block-container, [data-testid='stAppViewContainer'] { background: none !important; padding: 2rem 1rem !important; overflow: auto !important; }</style>", unsafe_allow_html=True)
    st.title(f"🍢 {st.session_state['user_info']['username']}님의 면접 코칭방")
    
    # 💡 [오류 해결 핵심] 피드백 리포트 메뉴 항목을 menu_list에 정식 추가하여 index 에러 해결!
    menu_list = ["📄 이력서 제출", "🤖 실전 면접방", "📊 면접 피드백"]
    menu = st.sidebar.radio("이동할 페이지 선택", menu_list, index=menu_list.index(st.session_state["current_menu"]))
    st.session_state["current_menu"] = menu

    if st.sidebar.button("로그아웃"):
        st.session_state.update({"logged_in": False, "user_info": None})
        for key in ["document_loaded", "db_data_fetched", "selected_company", "selected_job", "resume_text", "intro_text", "document_text", "interview_messages", "feedback_report"]:
            st.session_state.pop(key, None)
        st.rerun()

    if os.getenv("OPENAI_API_KEY"): st.caption("⚡ AI 엔진이 연결되었습니다.")
    else: st.error("⚠️ .env 파일에서 OPENAI_API_KEY를 확인해 주세요.")
    st.markdown("---")

    # 각 메뉴 페이지 렌더링 스위칭 연동 구역
    if menu == "📄 이력서 제출":
        document_page.render_document_page()
    elif menu == "🤖 실전 면접방":
        interview_page.render_interview_page()
    elif menu == "📊 면접 피드백":
        # 💡 [신규 추가] 피드백 전용 페이지 렌더링 함수 호출 연결
        feedback_page.render_feedback_page()