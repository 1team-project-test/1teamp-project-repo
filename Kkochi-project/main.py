'''
import os
import base64
import streamlit as st
import auth
import dashboard_manager as dm  # 💡 dashboard_manager.py 파일을 dm 이름으로 호출
import mariadb_control as db
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="꼬치꼬치 - AI 면접 코칭", page_icon="🍢", layout="wide")

# 세션 및 로그인 쿠키 복원 가동
saved_user_id = st.context.cookies.get("kkochi_session_user_id", "")
if "logged_in" not in st.session_state:
    if saved_user_id:
        with db.get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(db.N))
            cur.execute("SELECT * FROM {} WHERE user_id = %s".format(db.T), (saved_user_id,))
            user_record = cur.fetchone()
        if user_record:
            st.session_state.update({
                "logged_in": True, 
                "user_info": user_record
            })
            saved_resume = db.get_user_resume(saved_user_id)
            if saved_resume:
                st.session_state.update({
                    "selected_company": saved_resume.get("company", ""),
                    "selected_job": saved_resume.get("job", ""),
                    "interviewer_style": saved_resume.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)"),
                    "document_text": saved_resume.get("full_text", ""),
                    "document_loaded": True,
                    "db_data_fetched": True
                })
    else:
        st.session_state["logged_in"] = False

for key, default in [("user_info", None), ("show_auth_page", False), ("current_menu", "📄 이력서 제출")]:
    if key not in st.session_state:
        st.session_state[key] = default

if "trigger_auth" in st.query_params:
    st.query_params.clear()
    st.session_state["show_auth_page"] = True
    st.rerun()

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- 미로그인 / 로그인 화면 렌더링 분기 ---
if not st.session_state["logged_in"]:
    if st.session_state["show_auth_page"]:
        auth.render_auth_page()
    else:
        bg, btn = "bg.png", "startbutton.png"
        if os.path.exists(bg) and os.path.exists(btn):
            bg_url = f"data:image/png;base64,{get_base64_image(bg)}"
            btn_url = f"data:image/png;base64,{get_base64_image(btn)}"
            st.markdown(
                f"<style>"
                f"[data-testid='stHeader'] {{ display: none !important; }} "
                f".main, .block-container, [data-testid='stAppViewContainer'] {{ padding: 0 !important; margin: 0 !important; overflow: auto !important; }} "
                f".kkochi-screen-container {{ position: relative; width: 100vw; height: 100vh; min-width: 1200px; min-height: 700px; background: url('{bg_url}') no-repeat center center / cover; }} "
                f"/* 📌 유저님의 황금 좌표(65%, 53.3%) 자리에 고정해 클릭 영역 자석 일체화 */"
                f".kkochi-link-wrapper {{ position: absolute !important; top: 65% !important; left: 53.3% !important; width: 26% !important; aspect-ratio: 500 / 250 !important; transform: translate(-50%, -50%) !important; z-index: 9999 !important; }} "
                f".kkochi-responsive-btn {{ width: 100% !important; height: 100% !important; background: url('{btn_url}') no-repeat center center / contain !important; border: none !important; cursor: pointer !important; transition: transform 0.1s ease !important; }} "
                f".kkochi-responsive-btn:active {{ transform: scale(0.97) !important; }} "
                f"</style>"
                f"<div class='kkochi-screen-container'>"
                f"    <a href='?trigger_auth=true' target='_self' class='kkochi-link-wrapper'>"
                f"        <button class='kkochi-responsive-btn'></button>"
                f"    </a>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("⚠️ 이미지 파일이 유실되었습니다.")
else:
    st.markdown("<style>[data-testid='stHeader'], [data-testid='stSidebar'], [data-testid='stSidebarCollapseButton'] { display: none !important; } .main, .block-container { background-color: transparent !important; padding: 0 !important; }</style>", unsafe_allow_html=True)
    # 💡 [에러 해결 핀포인트 1] 오차 없이 함수 명세 선단을 완벽 매칭 전송 가동!
    dm.render_dashboard_layout()
'''
import os
import base64
import streamlit as st
import auth
import dashboard_manager as dm  # 💡 dashboard_manager.py 파일을 dm 이름으로 호출
import mariadb_control as db
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="꼬치꼬치 - AI 면접 코칭", page_icon="🍢", layout="wide")

# ─────────────── 💡 [새로고침 무적 가드 완치 핵심 1] ───────────────
# 주소창에서 유저님이 짚어주신 ?sid=user001 파라미터를 최우선으로 즉시 파싱합니다!
url_sid = st.query_params.get("sid", "")
saved_user_id = str(url_sid).strip() if url_sid else ""

# 💡 [새로고침 무적 가드 완치 핵심 2]
# 새로고침(F5)으로 인해 세션 상태가 완전히 포맷되더라도, 주소창에 sid 파라미터가 존재한다면 
# 대문 화면을 그리기 전에 MariaDB 레코드를 추적해 즉시 로그인 및 세션을 100% 강제 부활(True) 시킵니다!
if saved_user_id and saved_user_id != "":
    try:
        with db.get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(db.N))
            cur.execute("SELECT * FROM {} WHERE user_id = %s".format(db.T), (saved_user_id,))
            user_record = cur.fetchone()
            
        if user_record:
            # 📌 대문 화면 튕김 현상을 완전히 부수고, 내가 보던 대시보드 방으로 100% 도킹 복원!
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = user_record
            
            # 사내 MariaDB 보관함에서 예전 서류 데이터셋까지 연동 수송 완료
            saved_resume = db.get_user_resume(saved_user_id)
            if saved_resume and "db_data_fetched" not in st.session_state:
                st.session_state.update({
                    "selected_company": saved_resume.get("company", ""),
                    "selected_job": saved_resume.get("job", ""),
                    "interviewer_style": saved_resume.get("interviewer", "🔥 압박형 (날카로운 꼬리 질문)"),
                    "document_text": saved_resume.get("full_text", ""),
                    "document_loaded": True,
                    "db_data_fetched": True
                })
    except:
        pass

# 기본 세션 래퍼 관리 명세 보존
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

for key, default in [("user_info", None), ("show_auth_page", False), ("current_menu", "📄 이력서 제출")]:
    if key not in st.session_state:
        st.session_state[key] = default

if "trigger_auth" in st.query_params:
    st.query_params.clear()
    st.session_state["show_auth_page"] = True
    st.rerun()

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- 미로그인 / 로그인 화면 렌더링 분기 ---
if not st.session_state["logged_in"]:
    if st.session_state["show_auth_page"]:
        auth.render_auth_page()
    else:
        bg, btn = "bg.png", "startbutton.png"
        if os.path.exists(bg) and os.path.exists(btn):
            bg_url = f"data:image/png;base64,{get_base64_image(bg)}"
            btn_url = f"data:image/png;base64,{get_base64_image(btn)}"
            st.markdown(
                f"<style>"
                f"[data-testid='stHeader'] {{ display: none !important; }} "
                f".main, .block-container, [data-testid='stAppViewContainer'] {{ padding: 0 !important; margin: 0 !important; overflow: auto !important; }} "
                f".kkochi-screen-container {{ position: relative; width: 100vw; height: 100vh; min-width: 1200px; min-height: 700px; background: url('{bg_url}') no-repeat center center / cover; }} "
                f"/* 📌 유저님이 아침에 직접 셋팅 완료하신 황금 좌표(65%, 53.3%) 수치 1픽셀 오차 없이 대문 버튼 철통 고정 보존 */"
                f".kkochi-link-wrapper {{ position: absolute !important; top: 65% !important; left: 53.3% !important; width: 26% !important; aspect-ratio: 500 / 250 !important; transform: translate(-50%, -50%) !important; z-index: 9999 !important; }} "
                f".kkochi-responsive-btn {{ width: 100% !important; height: 100% !important; background: url('{btn_url}') no-repeat center center / contain !important; border: none !important; cursor: pointer !important; transition: transform 0.1s ease !important; }} "
                f".kkochi-responsive-btn:active {{ transform: scale(0.97) !important; }} "
                f"</style>"
                f"<div class='kkochi-screen-container'>"
                f"    <a href='?trigger_auth=true' target='_self' class='kkochi-link-wrapper'>"
                f"        <button class='kkochi-responsive-btn'></button>"
                f"    </a>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("⚠️ 이미지 파일이 유실되었습니다.")
else:
    # 💡 [새로고침 무적 가드 완치 핵심 3] 로그인에 성공해 대시보드가 열렸을 때 주소창에 ?sid= 형태로 파라미터가 유연하게 고정되도록 동기화 보정
    if "sid" not in st.query_params:
        st.query_params["sid"] = st.session_state["user_info"]["user_id"]
        
    st.markdown("<style>[data-testid='stHeader'], [data-testid='stSidebar'], [data-testid='stSidebarCollapseButton'] { display: none !important; } .main, .block-container { background-color: transparent !important; padding: 0 !important; }</style>", unsafe_allow_html=True)
    dm.render_dashboard_layout()

