import os
import re
import base64
import streamlit as st
import mariadb_control as db

def get_base64_image(image_path):
    with open(image_path, "rb") as f: return base64.b64encode(f.read()).decode()

def render_auth_page():
    bg_img_path = "background.png"  
    if os.path.exists(bg_img_path):
        bg_url = f"data:image/png;base64,{get_base64_image(bg_img_path)}"
        st.markdown(
            "<style>"
            "html, body, [data-testid='stApp'], [data-testid='stAppViewContainer'] { margin: 0 !important; padding: 0 !important; top: 0 !important; }"
            "div[data-testid='stAppViewContainer'], .main {"
            f"    background: url('{bg_url}') no-repeat center top !important; background-size: cover !important;"
            "    width: 100vw !important; min-height: 100vh !important; height: auto !important; overflow-y: auto !important;"
            "}"
            "[data-testid='stHeader'] { background: transparent !important; display: none !important; height: 0 !important; }"
            ".main .block-container { max-width: 650px !important; width: 100% !important; margin: 0 auto !important; padding: 0 !important; }"
            "[data-testid='stSubcontainer'], div[data-testid='stVerticalBlock'] > div:has(div[data-testid='stTabs']) {"
            "    background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important;"
            "    max-width: 650px !important; width: 100% !important; padding: 10px 40px 25px 40px !important; box-shadow: 0px 15px 35px rgba(0,0,0,0.1) !important;"
            "    position: fixed !important; left: 50% !important; top: 35% !important; transform: translateX(-50%) !important; z-index: 99999 !important;"
            "    max-height: 55vh !important; overflow-y: auto !important; overflow-x: hidden !important;"
            "}"
            "div[data-testid='stTextInput'] { margin-bottom: 8px !important; width: 100% !important; }"
            "div[data-testid='stTextInput'] label p { color: #1a202c !important; font-weight: 700 !important; margin-bottom: 4px !important; }"
            "div[data-testid='stTextInput'] input { background-color: #f8fafc !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; height: 38px !important; padding-left: 12px !important; }"
            "div[data-testid='stTabs'] button { font-weight: 800 !important; font-size: 15px !important; color: #4a5568 !important; padding: 8px 15px !important; }"
            "div[data-testid='stTabs'] button[aria-selected='true'] { color: #ff5232 !important; border-bottom: 3px solid #ff5232 !important; }"
            "div.back-btn-box { margin-top: -20px !important; width: 100% !important; }"
            "div.back-btn-box button { border-radius: 30px !important; margin: 0 0 12px 0 !important; font-size: 13px !important; border: 1px solid #e2e8f0 !important; background-color: #ffffff !important; color: #4a5568 !important; }"
            "div.stButton > button { background-color: #ff5232 !important; color: white !important; font-size: 15px !important; font-weight: 700 !important; border-radius: 8px !important; border: none !important; height: 42px !important; margin-top: 10px !important; width: 100% !important; }"
            "</style>", unsafe_allow_html=True
        )
    else: st.error("⚠️ 'background.png' 배경 파일이 없습니다.")

    with st.container():
        st.markdown('<div class="back-btn-box">', unsafe_allow_html=True)
        if st.button("⬅️ 메인 홈화면으로 돌아가기", key="back_to_main"):
            st.session_state["show_auth_page"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
        tab1, tab2 = st.tabs(["🔒 로그인", "📝 회원가입"])
        
        with tab1:
            login_id = st.text_input("아이디", key="login_id", placeholder="아이디를 입력하세요")
            login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="비밀번호를 입력하세요")
            
            btn_click = st.button("로그인하기", use_container_width=True, key="btn_login_submit")
            
            if btn_click or (login_id and login_pw and st.session_state.get("login_pw")):
                if login_id and login_pw:
                    user = db.authenticate_user(login_id, login_pw)
                    if user:
                        st.session_state.update({"logged_in": True, "user_info": user, "show_auth_page": False})
                        
                        # 💡 [오류 해결 핵심] 읽기 전용인 쿠키 대입 연산 대신, 공식 순정 주소창 파라미터 제어로 안전 수송 전환!
                        st.query_params["sid"] = str(user["user_id"])
                        
                        st.success("🎉 환영합니다!")
                        st.rerun()
                    else: st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
                else: st.warning("⚠️ 모든 필드를 입력해 주세요.")

        with tab2:
            reg_id = st.text_input("아이디 생성", key="reg_id", placeholder="사용할 로그인 ID")
            reg_pw = st.text_input("비밀번호 생성", type="password", key="reg_pw", placeholder="비밀번호 입력")
            if reg_pw:
                if bool(re.match(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", reg_pw)): st.success("✅ 안전한 비밀번호입니다!")
                else: st.error("❌ 영문, 숫자, 특수문자 조합 8자 이상 입력해야 합니다.")
            else: st.caption("※ 비밀번호는 영문, 숫자, 특수문자를 포함하여 8자 이상으로 설정해 주세요.")
            
            reg_name = st.text_input("이름", key="reg_name", placeholder="본인의 실명을 입력해 주세요")
            reg_email = st.text_input("이메일 주소", key="reg_email", placeholder="example@kkochi.com")
            reg_phone = st.text_input("전화번호", key="reg_phone", placeholder="010-0000-0000")
            
            if st.button("가입하기", use_container_width=True, key="btn_register_submit"):
                if all([reg_id, reg_pw, reg_name, reg_email, reg_phone]):
                    if not re.match(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", reg_pw): st.warning("⚠️ 비밀번호 조건을 다시 확인해 주세요.")
                    elif "@" not in reg_email: st.error("❌ 올바른 이메일 주소 형식이 아닙니다.")
                    elif db.register_user(reg_name, reg_id, reg_pw, reg_email, reg_phone): st.success("✅ 회원가입 성공!")
                else: st.warning("⚠️ 모든 항목을 빈칸 없이 채워주세요.")