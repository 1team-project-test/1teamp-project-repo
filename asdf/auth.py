import os
import base64
import streamlit as st
import mariadb_control as db

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def render_auth_page():
    bg_img_path = "background.png"  

    if os.path.exists(bg_img_path):
        bg_base64 = get_base64_image(bg_img_path)
        # CSS 스타일 속성들을 결합하여 라인 수 단축
        st.markdown(f"""
            <style>
            div[data-testid="stAppViewContainer"], .main, .block-container {{
                background: url("data:image/png;base64,{bg_base64}") no-repeat center fixed;
                background-size: 55% 100% !important; width: 100vw !important; max-width: 100vw !important; height: 100vh !important; padding: 0 !important; margin: 0 !important; overflow: hidden !important; 
            }}
            [data-testid="stHeader"] {{ background: transparent !important; display: none !important; }}
            .block-container {{ max-width: 550px !important; margin: calc(50vh - 260px) auto 0 auto !important; height: auto !important; }}
            div[data-testid="stTabs"], div[data-baseweb="tab-panel"], div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stTabs"]) {{
                background-color: #ffffff !important; border-radius: 16px !important; padding: 15px !important;               
            }}
            div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stTabs"]) {{ padding: 1.5rem 2rem 2.5rem 2rem !important; box-shadow: 0px 15px 40px rgba(0, 0, 0, 0.2) !important; }}
            div.back-btn-box button {{ border-radius: 20px !important; margin-bottom: 10px !important; font-size: 13px !important; }}
            div[data-testid="stTabs"] button {{ font-weight: bold !important; font-size: 15px !important; color: #555555 !important; background-color: transparent !important; }}
            div[data-testid="stTabs"] button[aria-selected="true"] {{ color: #ff5232 !important; border-bottom-color: #ff5232 !important; }}
            div[data-testid="stTextInput"] label p {{ color: #333333 !important; font-weight: bold !important; }}
            div[data-testid="stTextInput"] input {{ background-color: #f9fbfd !important; border: 1px solid #dcdcdc !important; border-radius: 6px !important; color: #333333 !important; height: 40px !important; }}
            div.stButton > button {{ background-color: #ff5232 !important; color: white !important; font-size: 16px !important; font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 46px !important; margin-top: 15px !important; box-shadow: 0px 4px 10px rgba(255, 82, 50, 0.2) !important; }}
            div.stButton > button:hover {{ background-color: #e04324 !important; }}
            </style>
        """, unsafe_allow_html=True)
    else:
        st.error(f"⚠️ '{bg_img_path}' 배경 파일을 찾을 수 없습니다.")

    st.markdown('<div class="back-btn-box">', unsafe_allow_html=True)
    if st.button("⬅️ 메인 홈화면으로 돌아가기", key="back_to_main"):
        st.session_state["show_auth_page"] = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔒 로그인", "📝 회원가입"])
    
    # --- 탭 1: 로그인 구역 ---
    with tab1:
        login_id = st.text_input("아이디", key="login_id", placeholder="아이디를 입력하세요")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="비밀번호를 입력하세요")
        
        if st.button("로그인하기", use_container_width=True, key="btn_login_submit"):
            if login_id and login_pw:
                user = db.authenticate_user(login_id, login_pw)
                if user:
                    st.session_state.update({"logged_in": True, "user_info": user, "show_auth_page": False})
                    st.success(f"🎉 {user['username']}님, 환영합니다!")
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.warning("⚠️ 모든 필드를 입력해 주세요.")

    # --- 탭 2: 회원가입 구역 ---
    with tab2:
        reg_id = st.text_input("아이디 생성", key="reg_id", placeholder="사용할 로그인 ID")
        reg_pw = st.text_input("비밀번호 생성", type="password", key="reg_pw", placeholder="비밀번호 입력")
        reg_name = st.text_input("이름", key="reg_name", placeholder="본인의 실명을 입력해 주세요")
        reg_email = st.text_input("이메일 주소", key="reg_email", placeholder="example@kkochi.com")
        reg_phone = st.text_input("전화번호", key="reg_phone", placeholder="010-0000-0000")
        
        if st.button("가입하기", use_container_width=True, key="btn_register_submit"):
            if all([reg_id, reg_pw, reg_name, reg_email, reg_phone]):
                if "@" not in reg_email:
                    st.error("❌ 올바른 이메일 주소 형식이 아닙니다.")
                elif db.register_user(reg_name, reg_id, reg_pw, reg_email, reg_phone):
                    st.success("✅ 회원가입 성공! 로그인 탭으로 이동해 주세요.")
            else:
                st.warning("⚠️ 모든 항목을 빈칸 없이 채워주세요.")