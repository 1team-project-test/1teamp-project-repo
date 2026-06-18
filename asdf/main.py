import os
import base64
import streamlit as st
from dotenv import load_dotenv
import auth

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
                "/* 1. 상단 헤더 숨김 및 가로/세로 스크롤 완전 개방 */"
                "[data-testid='stHeader'] { display: none !important; }"
                ".main, .block-container, [data-testid='stAppViewContainer'] {"
                "    width: auto !important; "
                "    height: auto !important; "
                "    padding: 0 !important; margin: 0 !important;"
                "    overflow-x: auto !important;"
                "    overflow-y: auto !important;"
                "}"
                ""
                "/* 2. 가로/세로 최소 크기를 고정하여 원본 일러스트 비율 완벽 보존 */"
                ".kkochi-screen-container {"
                "    position: relative;"
                "    width: 100vw;"
                "    height: 100vh;"
                "    min-width: 1200px;"
                "    min-height: 700px;"
                f"    background: url('{bg_url}') no-repeat center center / cover;"
                "}"
                ""
                "/* 3. 고정된 배경 위에 자석처럼 위치와 크기 비율을 모두 고수하는 버튼 */"
                ".kkochi-responsive-btn {"
                "    position: absolute;"
                "    top: 65% !important;"       
                "    left: 53.3% !important;"     
                "    /* 💡 가로너비 고정 px 대신 전체 너비 대비 비율(%) 단위 적용 */"
                "    width: 26% !important;"       # 💡 1920px 기준 약 500px 비율 유지
                "    aspect-ratio: 500 / 250 !important;" # 💡 500x250 원본 가로세로 비율 강제 유지 (종횡비 고정)
                "    max-width: 500px !important;"  # 너무 커지는 맥시멈 제한 지정 비율
                "    max-height: 250px !important;"
                "    transform: translate(-50%, -50%) !important;"
                f"    background: url('{btn_url}') no-repeat center center / contain !important;"
                "    border: none !important; cursor: pointer !important; z-index: 9999 !important;"
                "    transition: transform 0.1s ease !important;"
                "}"
                ".kkochi-responsive-btn:active { transform: translate(-50%, -50%) scale(0.97) !important; filter: brightness(0.9) !important; }"
                "</style>"
                ""
                "<!-- 배경과 버튼 박스 렌더링 -->"
                "<div class='kkochi-screen-container'>"
                "    <a href='?trigger_auth=true' target='_self'>"
                "        <button class='kkochi-responsive-btn'></button>"
                "    </a>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("⚠️ 배경 이미지(bg.png) 또는 버튼 이미지(startbutton.png)가 파일 경로에 없습니다.")

# --- 로그인 완료 화면 분기 ---
else:
    st.markdown("<style>.main, .block-container, [data-testid='stAppViewContainer'] { background: none !important; padding: 2rem 1rem !important; overflow: auto !important; }</style>", unsafe_allow_html=True)
    st.title(f"🍢 {st.session_state['user_info']['username']}님의 면접 코칭방")
    
    # 메뉴 제어 및 로그아웃
    menu_list = ["📄 이력서 제출", "🤖 실전 면접방"]
    menu = st.sidebar.radio("이동할 페이지 선택", menu_list, index=menu_list.index(st.session_state["current_menu"]))
    st.session_state["current_menu"] = menu

    if st.sidebar.button("로그아웃"):
        st.session_state.update({"logged_in": False, "user_info": None})
        st.session_state.pop("document_loaded", None)
        st.rerun()

    # API 키 검증 알림
    if os.getenv("OPENAI_API_KEY"): st.caption("⚡ AI 엔진이 연결되었습니다.")
    else: st.error("⚠️ .env 파일에서 OPENAI_API_KEY를 확인해 주세요.")
    st.markdown("---")

    