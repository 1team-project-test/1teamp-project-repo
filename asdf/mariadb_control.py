import os
import streamlit as st
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# 환경 변수 설정
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3307))
DB_USER = os.getenv("DB_USER", "scott")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "kkochi_db")
DB_TABLE = os.getenv("DB_TABLE", "kkochi_user")

def get_db_connection(select_db=True):
    """DB 연결 함수 (기본값으로 DB 선택 진입)"""
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
            database=DB_NAME if select_db else None
        )
    except mysql.connector.Error:
        return None

def initialize_database_automatically():
    """데이터베이스 및 회원 테이블 자동 생성"""
    conn = get_db_connection(select_db=False)
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8mb4;".format(DB_NAME))
        cursor.execute("USE {};".format(DB_NAME))
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS {} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(30) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """.format(DB_TABLE))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

initialize_database_automatically()

def register_user(username, user_id, password, email, phone):
    """[회원가입] 유저 등록"""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM {} WHERE user_id = %s".format(DB_TABLE), (user_id,))
        if cursor.fetchone():
            st.warning("이미 존재하는 아이디입니다.")
            return False
        
        cursor.execute(
            "INSERT INTO {} (username, user_id, password, email, phone) VALUES (%s, %s, %s, %s, %s)".format(DB_TABLE),
            (username, user_id, password, email, phone)
        )
        conn.commit()
        return True
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        conn.close()

def authenticate_user(user_id, password):
    """[로그인] 유저 인증"""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM {} WHERE user_id = %s AND password = %s".format(DB_TABLE), (user_id, password))
        return cursor.fetchone()
    except mysql.connector.Error:
        return None
    finally:
        cursor.close()
        conn.close()