import os
import streamlit as st
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
# 환경 변수 일괄 선언 및 변환 (U=scott 계정 반영)
H, P, U, PA, N, T = os.getenv("DB_HOST", "localhost"), int(os.getenv("DB_PORT", 3306)), os.getenv("DB_USER", "scott"), os.getenv("DB_PASS", ""), os.getenv("DB_NAME", "kkochi_db"), os.getenv("DB_TABLE", "kkochi_user")

def get_db(db=True):
    """DB 연결 코드를 한 줄로 요약"""
    return mysql.connector.connect(host=H, port=P, user=U, password=PA, database=N if db else None)

def initialize_database_automatically():
    """DB와 필수 테이블(회원/이력서) 생성을 하나의 실행 흐름으로 결합"""
    try:
        with get_db(db=False) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8mb4;".format(N))
                cur.execute("USE {};".format(N))
                
                # 1. 회원 정보 테이블 생성 (T 변수 연동)
                cur.execute("CREATE TABLE IF NOT EXISTS {} (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(50) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, username VARCHAR(50) NOT NULL, email VARCHAR(100) NOT NULL, phone VARCHAR(30) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;".format(T))
                
                # 2. 파싱 4대 핵심 데이터를 담을 최신 규격의 kkochi_resume TABLE 생성
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

# 💡 [오류 해결 핵심] 유실되었던 로그인 인증 함수를 다시 복구했습니다.
def authenticate_user(user_id, password):
    """[로그인] 유저 인증 및 회원 데이터 반환"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(N))
            cur.execute("SELECT * FROM {} WHERE user_id = %s AND password = %s".format(T), (user_id, password))
            return cur.fetchone()
    except: 
        return None

def save_parsed_resume(user_id, company, job, style, file_name, skills, exp, motiv, personality, raw_text):
    """[파싱 데이터 영구 저장] 변수명 매핑 오류 수정 완료"""
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("USE {};".format(N))
            sql = """
                INSERT INTO kkochi_resume 
                (user_id, company, job, interviewer, skills_and_specs, experience_projects, motivation, personality, full_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    company = VALUES(company),
                    job = VALUES(job),
                    interviewer = VALUES(interviewer),
                    skills_and_specs = VALUES(skills_and_specs),
                    experience_projects = VALUES(experience_projects),
                    motivation = VALUES(motivation),
                    personality = VALUES(personality),
                    full_text = VALUES(full_text)
            """
            cur.execute(sql, (user_id, company, job, style, skills, exp, motiv, personality, raw_text))
            conn.commit()
            return True
    except:
        return False
    
    # 💡 mariadb_control.py 최하단에 이어서 복사 붙여넣기 해주세요.
def get_user_resume(user_id):
    """[이력서/설정 불러오기] 로그인된 유저의 기존 면접 설정 및 파싱 서류 데이터를 DB에서 조회"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("USE {};".format(N))
            # kkochi_resume 테이블에서 해당 유저의 레코드를 딕셔너리 형태로 한 줄 추출
            cur.execute("SELECT * FROM kkochi_resume WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    except:
        return None