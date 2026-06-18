import os
import io
import json
import pymysql
import bcrypt
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
from openai import OpenAI

# .env 경로 명시적 설정
load_dotenv(dotenv_path=Path('C:/GG/Python/.env'))

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 클라이언트 초기화
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("경고: OPENAI_API_KEY가 로드되지 않았습니다! 경로를 확인하세요.")
client = OpenAI(api_key=api_key)

# DB 연결 함수
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# --- 모델 및 파싱 로직 ---

class SignUpModel(BaseModel):
    userName: str = "사용자"
    userId: str
    userPw: str
    userPhone: str
    userEmail: str

class LoginModel(BaseModel):
    userId: str
    userPw: str

def parse_document_via_ai(text_content):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "너는 이력서 전문 파서 엔진이다. 다음 4개 키를 가진 JSON으로 응답해라: 'skills_and_specs', 'experience_projects', 'motivation', 'personality'."},
                {"role": "user", "content": text_content}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI 파싱 에러: {e}")
        return {"skills_and_specs": "", "experience_projects": "", "motivation": "", "personality": ""}

# --- API 엔드포인트 ---

@app.post("/signup")
def signup(data: SignUpModel):
    conn = get_db_connection()
    try:
        password_bytes = data.userPw.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (user_name, user_id, user_pw, user_phone, user_email) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (data.userName, data.userId, hashed_password, data.userPhone, data.userEmail))
        conn.commit()
        return {"status": "success", "message": "회원가입 성공!"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}
    finally:
        conn.close()

@app.post("/login")
def login(data: LoginModel):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT user_id, user_pw, user_name FROM users WHERE user_id = %s"
            cursor.execute(sql, (data.userId,))
            user = cursor.fetchone()
            if not user or not bcrypt.checkpw(data.userPw.encode('utf-8'), user['user_pw'].encode('utf-8')):
                return {"status": "fail", "message": "아이디 또는 비밀번호가 잘못되었습니다."}
            return {"status": "success", "user_name": user['user_name'], "user_id": user['user_id']}
    finally:
        conn.close()

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...), 
    user_id: str = Form(...) 
):
    conn = None
    try:
        content = await file.read()
        file_name = file.filename
        
        if file.filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            full_text = "\n".join([para.text for para in doc.paragraphs])
        else:
            full_text = content.decode("utf-8", errors='ignore')
            
        conn = get_db_connection()
        # 💡 수정: 명시적으로 DictCursor를 장착해 꼬임을 방지합니다.
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. 중복 체크
            check_sql = "SELECT resume_id FROM user_resumes WHERE user_id = %s AND raw_text = %s"
            cursor.execute(check_sql, (user_id, full_text))
            if cursor.fetchone():
                return {"status": "fail", "message": "이미 동일한 내용의 이력서가 등록되어 있습니다."}
            
            # 2. AI 파싱 및 저장
            parsed_result = parse_document_via_ai(full_text)
            
            sql = """INSERT INTO user_resumes 
                     (user_id, file_name, skills, experience, motivation, personality, raw_text) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(sql, (
                user_id, 
                file_name, 
                json.dumps(parsed_result.get("skills_and_specs", ""), ensure_ascii=False), 
                json.dumps(parsed_result.get("experience_projects", ""), ensure_ascii=False),
                json.dumps(parsed_result.get("motivation", ""), ensure_ascii=False),
                json.dumps(parsed_result.get("personality", ""), ensure_ascii=False),
                full_text
            ))
        
        conn.commit()
        return {"status": "success", "message": "저장 완료", "data": parsed_result}

    except Exception as e:
        if conn: conn.rollback()
        print(f"백엔드 업로드 예외 발생: {str(e)}") # 터미널 콘솔 로그에 원인을 찍어줍니다.
        return {"status": "fail", "message": f"서버 내부 에러: {str(e)}"}
    finally:
        if conn: conn.close()

@app.post("/check-id")
def check_id(data: dict):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT user_id FROM users WHERE user_id = %s"
            cursor.execute(sql, (data.get("userId"),))
            result = cursor.fetchone()
        return {"status": "fail" if result else "success"}
    finally:
        conn.close()

@app.get("/get-resumes")
def get_resumes(user_id: str):
    conn = get_db_connection()
    try:
        # 💡 수정: 일관성 있게 명시적 DictCursor 사용
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT resume_id, file_name, LEFT(raw_text, 20) as preview FROM user_resumes WHERE user_id = %s ORDER BY resume_id DESC"
            cursor.execute(sql, (user_id,))
            return {"status": "success", "data": cursor.fetchall()}
    finally:
        conn.close()

# --- 면접 및 LLM 관련 Pydantic 모델 정의 ---
class StartInterviewModel(BaseModel):
    user_id: str
    company: str
    job: str
    style: str
    resume_id: str

class NextQuestionModel(BaseModel):
    messages: list

# --- [추가] 1. 면접 시작 및 초기 프롬프트/인사말 생성 API ---
@app.post("/start-interview")
def start_interview(data: StartInterviewModel):
    conn = get_db_connection()
    try:
        # DB에서 선택한 이력서의 원본 텍스트(raw_text) 가져오기
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT raw_text FROM user_resumes WHERE resume_id = %s AND user_id = %s"
            cursor.execute(sql, (data.resume_id, data.user_id))
            resume = cursor.fetchone()
        
        # 이력서가 없거나 에러가 날 경우를 대비한 방어 코드
        doc_text = resume['raw_text'] if resume else "등록된 이력서 정보가 없습니다."

        # Streamlit에 있던 베테랑 면접관 시스템 프롬프트 주입
        system_prompt = f"""
        너는 {data.company}의 {data.job} 채용을 담당하는 베테랑 AI 면접관이다.
        현재 면접 대상자의 이력서 및 자기소개서 데이터를 바탕으로 1:1 면접을 진행하고 있다.
        
        [⚠️ 중요 규칙 - 반드시 준수할 것]
        1. 질문은 무조건 한 번에 '딱 한 개'씩만 던져라.
        2. 실제 면접관처럼 일관되게 자연스럽고 격식 있는 한국어 경어체를 사용해라.
        3. 모든 답변은 반드시 100% 한국어여야만 한다. 절대 영어로 답변하지 마라.
        4. 지원자의 답변 내용을 바탕으로 본격적인 {data.style} 성향에 맞춘 날카롭거나 공감어린 다음 면접 꼬리 질문을 한국어로 전개해라.
        5. 지원자가 오타나 잘못된 말을 하면 한번 더 설명 해 달라 요구한다.
        
        [지원자 서류 본문 데이터]
        {doc_text}
        """

        # 면접관 성향(style)에 따른 맞춤형 첫 인사말 고정 분기
        if "압박" in data.style:
            style_intro = f"안녕하십니까. {data.company}의 {data.job} 직무 면접을 맡은 면접관입니다. 바로 긴장감 있게 진행해 보죠."
        elif "부드러운" in data.style:
            style_intro = f"안녕하세요! 오늘 {data.company}의 {data.job} 직무 면접을 진행하게 되어 반갑습니다. 편안한 마음으로 임해주세요."
        else:
            style_intro = f"반갑습니다. {data.company}의 {data.job} 직무 채용 면접관입니다. 대답의 논리성과 사실 관계를 중심으로 평가하겠습니다."

        initial_q = f"{style_intro}\n\n먼저 가볍게 **1분 자기소개**부터 부탁드립니다."

        # 프론트엔드가 기억하고 누적할 초기 메시지 셋 구축
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": initial_q}
        ]

        return {"status": "success", "messages": messages}
    
    except Exception as e:
        print(f"면접 세션 생성 중 예외 발생: {str(e)}")
        return {"status": "fail", "message": f"서버 에러: {str(e)}"}
    finally:
        conn.close()

# --- [추가] 2. 실시간 로컬 Ollama API 호출 및 다음 질문 생성 API ---
@app.post("/get-next-question")
def get_next_question(data: NextQuestionModel):
    try:
        # 로컬 Ollama 환경(gemma2:9b 등)을 호출하기 위한 독립 OpenAI 클라이언트 설정
        ollama_client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="gemma2" # 로컬 오토 토큰 우회용 키값
        )
        
        response = ollama_client.chat.completions.create(
            model="gemma2:9b", # 💡 실제 설치 및 다운로드된 모델명 기입
            messages=data.messages,
            temperature=0.5
        )
        
        if hasattr(response, "choices") and len(response.choices) > 0:
            next_q = response.choices[0].message.content
            return {"status": "success", "next_question": next_q}
        
        return {"status": "fail", "message": "AI 면접관의 응답 형식이 올바르지 않습니다."}
        
    except Exception as e:
        print(f"Ollama 연동 에러: {e}")
        return {"status": "fail", "message": f"AI 면접관 통신 장애: {str(e)}"}
    
# --- [추가] 3. 면접 종료 및 전체 대화 분석 피드백 리포트 생성 API ---
class EndInterviewModel(BaseModel):
    interview_messages: list  # 프론트엔드에서 쌓인 대화 기록 배열

@app.post("/end-interview")
def end_interview(data: dict): # 💡 BaseModel 대신 dict로 유연하게 받음
    try:
        # 프론트엔드가 보낼 수 있는 후보 키들을 유연하게 매핑
        messages_list = data.get("interview_messages") or data.get("messages") or data.get("chatHistory")
        
        if not messages_list or not isinstance(messages_list, list):
            print(f"받은 데이터 구조: {data}") # 터미널에 구조 출력해서 디버깅용
            return {"status": "fail", "message": "대화 기록 배열(list)을 찾을 수 없습니다."}

        # 1. 대화 기록 가공
        conversation_log = ""
        for msg in messages_list:
            if msg.get("role") == "assistant":
                conversation_log += f"면접관: {msg.get('content')}\n"
            elif msg.get("role") == "user":
                conversation_log += f"지원자: {msg.get('content')}\n"

        if not conversation_log.strip():
            return {"status": "fail", "message": "분석할 면접 대화 기록이 존재하지 않습니다."}

        # 2. 로컬 Ollama API 호출
        ollama_client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        
        system_feedback_prompt = (
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

        response = ollama_client.chat.completions.create(
            model="gemma2:9b",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": system_feedback_prompt},
                {"role": "user", "content": f"이하 면접 대화 기록을 분석하여 리포트를 작성해라:\n{conversation_log}"}
            ],
            temperature=0.3
        )
        
        if hasattr(response, "choices") and len(response.choices) > 0:
            feedback_json = json.loads(response.choices[0].message.content)
            return {"status": "success", "report": feedback_json}
            
        return {"status": "fail", "message": "AI 면접관의 피드백 응답 형식이 올바르지 않습니다."}
        
    except Exception as e:
        print(f"[Ollama Feedback Error] 상세 원인: {e}")
        return {"status": "fail", "message": f"서버 내부 에러: {str(e)}"}