import streamlit as st
from db_handler import get_latest_feedback

st.set_page_config(page_title="면접 결과 피드백", layout="wide")

st.title("📊 AI 면접 결과 리포트")
st.write("이번 면접 세션의 대화 내용을 바탕으로 인공지능이 분석한 결과입니다.")
st.write("---")

# DB에서 가장 최근에 생성된 피드백 가져오기
feedback = get_latest_feedback()

if not feedback:
    st.info("아직 완료된 면접 피드백 리포트가 없습니다. 면접을 먼저 진행해 주세요.")
    if st.button("면접실로 이동하기"):
        st.switch_page("pages/2_Interview.py")
    st.stop()

# 1. 종합 점수 대시보드
col1, col2 = st.columns([1, 3])
with col1:
    st.metric(label="🎖️ 종합 점수", value=f"{feedback['overall_score']} / 100점")
with col2:
    st.subheader(f"분석 직무: {feedback['job_title']}")
    st.caption(f"평가 일시: {feedback['created_at']}")

st.write("---")

# 2. 상세 피드백 영역 (Tabs 구성으로 깔끔하게 레이아웃 분리)
tab1, tab2, tab3 = st.tabs(["✨ 잘한 점 (Strengths)", "⚠️ 아쉬운 점 (Weaknesses)", "🚀 개선 방향 (Action Items)"])

with tab1:
    st.success("### 면접관을 사로잡은 답변 포인트")
    st.write(feedback['good_points'])

with tab2:
    st.warning("### 보완이 필요한 감점 요인")
    st.write(feedback['bad_points'])

with tab3:
    st.info("### 다음 면접을 위한 합격 팁")
    st.write(feedback['improvement_tips'])

st.write("---")

# 3. 재도전 버튼
if st.button("🔄 새로운 면접 시작하기", type="primary"):
    # 필요 시 세션이나 DB 초기화 로직 추가 가능
    st.switch_page("pages/1_Setting.py")