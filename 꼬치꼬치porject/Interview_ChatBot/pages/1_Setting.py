import streamlit as st
from PIL import Image
import pytesseract
import os # 경로 확인을 위해 추가

# ⚠️ [핵심] Tesseract 프로그램 실행 파일 경로를 직접 지정합니다.
# 윈도우 기본 설치 경로입니다. 만약 다른 곳에 설치하셨다면 그 경로를 적어주세요.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("📋 면접 설정")
st.write("면접을 시작하기 전 정보를 입력하고 이력서 이미지를 업로드해 주세요.")

# 세션 상태 초기화
if "job_title" not in st.session_state:
    st.session_state.job_title = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# 1. 직무 입력
job = st.text_input("지원할 직무를 입력하세요 (예: 백엔드 개발자)", value=st.session_state.job_title)

# 2. 이력서 이미지 업로드
uploaded_file = st.file_uploader("이력서 이미지를 업로드하세요 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])

# 이미지가 업로드되었을 때 처리
if uploaded_file is not None:
    # 이미지 화면에 띄우기
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 이력서 이미지", use_container_width=True)
    
    # OCR 텍스트 추출 버튼
    if st.button("이력서 이미지에서 텍스트 추출하기"):
        with st.spinner("이미지에서 글자를 읽어오는 중입니다..."):
            try:
                # pytesseract를 이용해 한글(kor)과 영어(eng) 추출
                extracted_text = pytesseract.image_to_string(image, lang="kor+eng")
                st.session_state.resume_text = extracted_text
                st.success("텍스트 추출 성공!")
            except Exception as e:
                st.error("OCR 엔진을 찾을 수 없거나 에러가 발생했습니다. Tesseract 설치를 확인하세요.")

# 3. 추출된 텍스트 확인 및 최종 저장
if st.session_state.resume_text:
    st.subheader("📝 추출된 이력서 내용")
    # 추출이 완벽하지 않을 수 있으므로 사용자가 직접 수정 가능하도록 text_area로 보여줌
    final_resume = st.text_area("추출된 내용을 확인하고 필요한 경우 수정하세요.", value=st.session_state.resume_text, height=250)
else:
    final_resume = ""

st.write("---")

# 최종 저장 버튼
if st.button("설정 저장하고 면접실 이동하기"):
    if not job or not final_resume:
        st.warning("직무 입력과 이력서 텍스트 추출을 모두 완료해 주세요.")
    else:
        st.session_state.job_title = job
        st.session_state.resume_text = final_resume
        st.success("정보가 저장되었습니다! '2_Interview' 페이지로 이동해서 면접을 시작하세요.")