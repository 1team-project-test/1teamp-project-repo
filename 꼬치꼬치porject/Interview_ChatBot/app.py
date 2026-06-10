import streamlit as st
from db_handler import create_tables, create_feedback_table

# 💡 두 테이블 생성 함수를 모두 실행합니다.
create_tables()
create_feedback_table()

st.set_page_config(page_title="면접 꼬리질문 챗봇", layout="wide")


st.title("🎯 AI 면접 꼬리질문 챗봇 프로젝트")
st.write("---")
st.subheader("환영합니다! 실전 같은 면접을 경험해 보세요.")
st.markdown("""
1. 왼쪽 사이드바에서 **1_Setting**을 선택해 이력서와 직무를 등록하세요.
2. 등록 후 **2_Interview**로 이동해 AI와 압박 면접을 시작하세요.
3. AI는 당신의 답변을 기반으로 날카로운 **꼬리질문**을 던집니다.
""")