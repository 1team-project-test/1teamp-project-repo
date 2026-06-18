import os
import json
import base64
import streamlit as st
from openai import OpenAI
import mariadb_control as db

# 1. 배경 이미지를 Base64로 인코딩하여 CSS에 삽입하는 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return ""

# [프롬프트 유지] 로직 수정 없음
def generate_interview_feedback(history_messages):
    """Ollama 로컬 API를 활용해 전체 면접 대화 이력을 분석하여 리포트 생성"""
    try:
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        
        conversation_log = ""
        for msg in history_messages:
            if msg["role"] == "assistant":
                conversation_log += "면접관: {}\n".format(msg["content"])
            elif msg["role"] == "user":
                conversation_log += "지원자: {}\n".format(msg["content"])
        
        response = client.chat.completions.create(
            model="gemma2:9b",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "당신은 10년 차 베테랑 채용 팀장이자 기업 면접관입니다. 지원자의 면접 대화록을 심층 분석하여 다음 5가지 항목을 포함한 JSON으로 응답하세요.\n\n"
                        "1. total_score (0~100점): 답변의 논리성, 직무 연관성, 태도를 종합적으로 평가한 정수 점수.\n"
                        "2. grade (S/A/B/C/D): 점수에 따른 합격 가능성 등급.\n"
                        "3. strengths: 지원자가 대화 중 보여준 긍정적인 역량 3가지 이상을 구체적 근거와 함께 서술.\n"
                        "4. weaknesses: 답변의 논리적 허점, 부족한 수치적 근거, 모호한 표현 등 보완이 필요한 점 3가지 이상을 구체적 예시와 함께 서술.\n"
                        "5. best_answer_guide: 면접관이 기대했던 수준 높은 모범 답안의 구조와 핵심 내용을 정리한 코칭 가이드.\n\n"
                        "⚠️ 필수 작성 규칙:\n"
                        "- 모든 분석은 200자 이상의 풍성한 한글 문장으로 정성스럽게 작성할 것.\n"
                        "- 단순한 요약이 아니라, 왜 그렇게 평가했는지 '이유'를 명확히 제시할 것.\n"
                        "- JSON 데이터 외에는 어떤 서론, 결론, 마크다운 기호도 포함하지 말고 오직 JSON만 출력할 것.\n"
                        "- 피드백은 100% 전문적인 한글 경어체로 작성할 것."
                    )
                },
                {"role": "user", "content": "이하 면접 대화 기록을 분석하여 리포트를 작성해라:\n{}".format(conversation_log)}
            ],
            temperature=0.3
        )
        
        if hasattr(response, "choices") and len(response.choices) > 0:
            return json.loads(response.choices[0].message.content)
        return None
    except Exception as e:
        print("[Ollama Feedback Error] 상세 원인: {}".format(e))
        return None

def render_feedback_page():
    # 1. 배경 이미지 로드
    img_data = get_base64_image("background.png")
    
    # 2. 확실한 CSS 적용 (전체 컨테이너를 타겟팅)
    st.markdown(f"""
        <style>
        /* 페이지 전체 배경 고정 */
        .stApp {{
            background-image: url("data:image/png;base64,{img_data}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* 스트림릿 기본 배경 흰색을 투명하게 제거 */
        section[data-testid="stAppViewContainer"] {{
            background-color: transparent !important;
        }}
        
        /* 메인 콘텐츠를 감싸는 흰색 박스 (화면 중앙 정렬 및 여백 확보) */
        .report-wrapper {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid #E5D3B3;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            max-width: 900px;
            margin: 50px auto; /* 중앙 정렬 */
        }}
        
        /* 메트릭 카드 스타일 */
        [data-testid="stMetric"] {{ 
            background-color: #FFFFFF; 
            padding: 20px; 
            border-radius: 15px; 
            border: 1px solid #E5D3B3; 
        }}
        [data-testid="stMetricValue"] {{ color: #8B4513 !important; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

    # 3. HTML 래퍼 시작
    st.markdown('<div class="report-wrapper">', unsafe_allow_html=True)
    
    st.subheader("📊 AI 면접 채점 및 종합 피드백 리포트")
    st.caption("AI 채용 전문가가 지원자님의 역량을 따뜻하고 꼼꼼하게 분석했습니다.")
    st.markdown("---")

    # 데이터 로직
    if "interview_messages" not in st.session_state or len(st.session_state["interview_messages"]) <= 2:
        st.warning("⚠️ 면접 대화 기록이 존재하지 않습니다.")
    elif "feedback_report" not in st.session_state:
        st.info("ℹ️ 분석된 피드백 리포트가 없습니다.")
    else:
        report = st.session_state["feedback_report"]
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="💯 종합 채점 점수", value="{} / 100 점".format(report.get("total_score", 0)))
        with col2:
            st.metric(label="🏅 예상 합격 등급", value="[{}] 등급".format(report.get("grade", "B")))

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("✨ 지원자님의 핵심 강점 (Strengths)", expanded=True):
            st.write(report.get("strengths", "분석된 내용이 없습니다."))
        with st.expander("⚠️ 아쉬운 점 및 취약점 (Weaknesses)", expanded=True):
            st.write(report.get("weaknesses", "분석된 내용이 없습니다."))
        with st.expander("💡 면접관이 제안하는 핵심 모범 답안 가이드 (Coaching)", expanded=True):
            st.write(report.get("best_answer_guide", "분석된 내용이 없습니다."))

        st.markdown("---")
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔄 면접 다시 도전하기"):
                st.session_state.pop("interview_messages", None); st.session_state.pop("feedback_report", None)
                st.session_state["current_menu"] = "🤖 실전 면접방"; st.rerun()
        with b2:
            if st.button("📄 새로운 서류 제출"):
                st.session_state["current_menu"] = "📄 이력서 제출"; st.rerun()

    # 4. HTML 래퍼 닫기
    st.markdown('</div>', unsafe_allow_html=True)