import os
import streamlit as st
import mysql.connector
import json
from dotenv import load_dotenv

load_dotenv()
# 환경 변수 일괄 선언
H, P, U, PA, N, T = os.getenv("DB_HOST", "localhost"), int(os.getenv("DB_PORT", 3306)), os.getenv("DB_USER", "scott"), os.getenv("DB_PASS", ""), os.getenv("DB_NAME", "kkochi_db"), os.getenv("DB_TABLE", "kkochi_user")

def get_db(db=True):
    return mysql.connector.connect(host=H, port=P, user=U, password=PA, database=N if db else None)

def initialize_database_automatically():
    """데이터 보존을 위해 DROP 문을 제거하고 IF NOT EXISTS 사용"""
    try:
        with get_db(db=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {N} DEFAULT CHARACTER SET utf8mb4;")
                cur.execute(f"USE {N};")
                
                # 1. 회원 정보 테이블
                cur.execute(f"""CREATE TABLE IF NOT EXISTS {T} (
                    id INT AUTO_INCREMENT PRIMARY KEY, 
                    user_id VARCHAR(50) NOT NULL UNIQUE, 
                    password VARCHAR(255) NOT NULL, 
                    username VARCHAR(50) NOT NULL, 
                    email VARCHAR(100) NOT NULL, 
                    phone VARCHAR(30) NOT NULL, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""")
                
                # 2. 이력서 테이블
                cur.execute("""CREATE TABLE IF NOT EXISTS kkochi_resume (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""")
                
                # 3. 히스토리 테이블
                cur.execute("""CREATE TABLE IF NOT EXISTS kkochi_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    company VARCHAR(100) NOT NULL,
                    job VARCHAR(100) NOT NULL,
                    interviewer_style VARCHAR(100) NOT NULL,
                    chat_log LONGTEXT NOT NULL,
                    feedback_log LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""")
                conn.commit()
    except Exception as e:
        print(f"DB 초기화 오류: {e}")

# --- 로그인 정보 복구용 함수 추가 (핵심) ---
def get_user_info_by_id(user_id):
    """쿠키에 저장된 user_id를 기반으로 DB에서 사용자 정보를 재조회하는 함수"""
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(f"USE {N};")
            cur.execute(f"SELECT * FROM {T} WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    except Exception as e:
        print(f"로그인 정보 복구 중 오류 발생: {e}")
        return None

# --- 데이터 관리 함수들 ---
def delete_interview_history(history_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"USE {N};")
                cur.execute("DELETE FROM kkochi_history WHERE id = %s", (history_id,))
                conn.commit()
                return True
    except: 
        return False

def register_user(username, user_id, password, email, phone):
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {T} WHERE user_id = %s", (user_id,))
            if cur.fetchone(): return False
            cur.execute(f"INSERT INTO {T} (username, user_id, password, email, phone) VALUES (%s, %s, %s, %s, %s)", (username, user_id, password, email, phone))
            conn.commit()
            return True
    except: return False

def authenticate_user(user_id, password):
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(f"USE {N};")
            cur.execute(f"SELECT * FROM {T} WHERE user_id = %s AND password = %s", (user_id, password))
            return cur.fetchone()
    except: return None

def save_parsed_resume(user_id, company, job, style, file_name, skills, exp, motiv, personality, raw_text):
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(f"USE {N};")
            sql = """INSERT INTO kkochi_resume (user_id, company, job, interviewer, skills_and_specs, experience_projects, motivation, personality, full_text) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
                     ON DUPLICATE KEY UPDATE company=VALUES(company), job=VALUES(job), interviewer=VALUES(interviewer), skills_and_specs=VALUES(skills_and_specs), 
                     experience_projects=VALUES(experience_projects), motivation=VALUES(motivation), personality=VALUES(personality), full_text=VALUES(full_text)"""
            cur.execute(sql, (user_id, company, job, style, skills, exp, motiv, personality, raw_text))
            conn.commit()
            return True
    except: return False

def get_user_resume(user_id):
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(f"USE {N};")
            cur.execute("SELECT * FROM kkochi_resume WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    except: return None

def save_interview_and_feedback_together(user_id, company, job, style, chat_messages, feedback_json):
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(f"USE {N};")
            clean_log = json.dumps([m for m in chat_messages if m["role"] != "system"], ensure_ascii=False)
            f_log = json.dumps(feedback_json, ensure_ascii=False)
            sql = "INSERT INTO kkochi_history (user_id, company, job, interviewer_style, chat_log, feedback_log) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (user_id, company, job, style, clean_log, f_log))
            conn.commit()
            return True
    except: return False

def get_user_interview_histories(user_id):
    try:
        with get_db() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(f"USE {N};")
            cur.execute("SELECT * FROM kkochi_history WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return cur.fetchall()
    except: return []