import os
import streamlit as st
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
# 환경 변수 일괄 선언 및 변환
H, P, U, PA, N, T = os.getenv("DB_HOST", "localhost"), int(os.getenv("DB_PORT", 3306)), os.getenv("DB_USER", "scott"), os.getenv("DB_PASS", ""), os.getenv("DB_NAME", "kkochi_db"), os.getenv("DB_TABLE", "kkochi_user")

def get_db(db=True):
    """DB 연결 코드를 한 줄로 요약"""
    return mysql.connector.connect(host=H, port=P, user=U, password=PA, database=N if db else None)

def initialize_database_automatically():
    """DB와 필수 테이블(회원/이력서/히스토리) 생성을 하나의 실행 흐름으로 결합 및 리빌드"""
    try:
        with get_db(db=False) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8mb4;".format(N))
                cur.execute("USE {};".format(N))
                
                # 1. 회원 정보 테이블 생성 (T 변수 연동)
                cur.execute("CREATE TABLE IF NOT EXISTS {} (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(50) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, username VARCHAR(50) NOT NULL, email VARCHAR(100) NOT NULL, phone VARCHAR(30) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;".format(T))
                
                # 2. 파싱 4대 핵심 데이터를 담을 최신 규격의 kkochi_resume 테이블 신설
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS kkochi_resume (
                        user_id VARCHAR(50) PRIMARY KEY,
                        company VARCHAR(100) NOT NULL,
                        job VARCHAR(100) NOT NULL,
                        interviewer VARCHAR(100) NOT NULL,
                        skills_and_specs TEXT,
                        experience_projects TEXT,
                        motivation TEXT,
                        personality TEXT,
                        full_text TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                
                # 3. 대용량 대화록 보관을 위한 kkochi_history 테이블 신설 (LONGTEXT 반영)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS kkochi_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(50) NOT NULL,
                        company VARCHAR(100) NOT NULL,
                        job VARCHAR(100) NOT NULL,
                        interviewer_style VARCHAR(100) NOT NULL,
                        chat_log LONGTEXT NOT NULL,
                        feedback_log LONGTEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                conn.commit()
    except: pass

initialize_database_automatically()

def register_user(username, user_id, password, email, phone):
    """[회원가입] 구조 압축"""
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM {} WHERE user_id = %s".format(T), (user_id,))
            if cur.fetchone():
                st.warning("이미 존재하는 아이디입니다.")
                return False
            cur.execute("INSERT INTO {} (username, user_id, password, email, phone) VALUES (%s, %s, %s, %s, %s)".format(T), (username, user_id, password, email, phone))
            conn.commit()
            return True
    except: return False

def authenticate_user(user_id, password):
    """[로그인] 구조 압축"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(N))
            cur.execute("SELECT * FROM {} WHERE user_id = %s AND password = %s".format(T), (user_id, password))
            return cur.fetchone()
    except: return None

def save_parsed_resume(user_id, company, job, style, file_name, skills, exp, motiv, personality, raw_text):
    """[파싱 데이터 영구 저장] 구조 압축"""
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            sql = """
                INSERT INTO kkochi_resume 
                (user_id, company, job, interviewer, skills_and_specs, experience_projects, motivation, personality, full_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    company = VALUES(company), job = VALUES(job), interviewer = VALUES(interviewer),
                    skills_and_specs = VALUES(skills_and_specs), experience_projects = VALUES(experience_projects),
                    motivation = VALUES(motivation), personality = VALUES(personality), full_text = VALUES(full_text)
            """
            cur.execute(sql, (user_id, company, job, style, skills, exp, motiv, personality, raw_text))
            conn.commit()
            return True
    except: return False

def get_user_resume(user_id):
    """[이력서/설정 불러오기] 로그인된 유저의 기존 면접 설정 및 파싱 서류 데이터를 DB에서 조회"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(N))
            cur.execute("SELECT * FROM kkochi_resume WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    except: return None

def save_interview_history(user_id, company, job, style, chat_messages):
    """[면접 최초 시작/종료] 1단계로 실시간 대화 히스토리 로그만 먼저 DB에 생성하고 생성된 행 ID 반환"""
    try:
        import json
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            clean_log = json.dumps([m for m in chat_messages if m["role"] != "system"], ensure_ascii=False)
            sql = "INSERT INTO kkochi_history (user_id, company, job, interviewer_style, chat_log) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(sql, (user_id, company, job, style, clean_log))
            conn.commit()
            return cur.lastrowid
    except: return None

def update_interview_feedback(history_id, feedback_json):
    """[AI 피드백 조각 수정] 2단계로 면접방 종료 버튼 클릭 시 GPT가 연산한 레포트 JSON을 히스토리 행에 최종 패치"""
    try:
        import json
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            f_log = json.dumps(feedback_json, ensure_ascii=False)
            sql = "UPDATE kkochi_history SET feedback_log = %s WHERE id = %s"
            cur.execute(sql, (f_log, history_id))
            conn.commit()
            return True
    except: return False

def save_interview_and_feedback_together(user_id, company, job, style, chat_messages, feedback_json):
    """[이력/피드백 원스톱 통합 저장] 단 한 번의 트랜잭션으로 대용량 세트를 안전하게 보관함 적재"""
    try:
        import json
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            clean_log = json.dumps([m for m in chat_messages if m["role"] != "system"], ensure_ascii=False)
            f_log = json.dumps(feedback_json, ensure_ascii=False)
            sql = "INSERT INTO kkochi_history (user_id, company, job, interviewer_style, chat_log, feedback_log) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (user_id, company, job, style, clean_log, f_log))
            conn.commit()
            return True
    except: return False

def get_user_interview_histories(user_id):
    """[면접 기록 목록 조회] 해당 유저가 과거에 진행했던 모든 면접 및 피드백 이력 세트 추출"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(N))
            cur.execute("SELECT * FROM kkochi_history WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return cur.fetchall()
    except: return []

# 💡 [신규 추가] 면접 기록 선택 삭제 기능 함수 (get_db 연동 완료)
def delete_user_interview_history(user_id, created_at):
    """🗑️ 유저의 특정 면접 기록을 생성 시간(created_at) 기준으로 영구 삭제합니다."""
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            # user_id와 고유 생성시간(created_at)이 완벽히 일치하는 행을 타겟팅하여 삭제
            sql = "DELETE FROM kkochi_history WHERE user_id = %s AND created_at = %s"
            cur.execute(sql, (user_id, created_at))
            conn.commit()
            return True
    except Exception as e:
        raise e