import mysql.connector

def get_db_connection():
    # 본인의 MariaDB 정보에 맞게 수정하세요.
    return mysql.connector.connect(
        host="localhost",
        user="scott",
        password="tiger",
        database="python_schema"
    )

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 면접 세션 및 대화 기록을 저장할 기본 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(10) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_message(role, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_logs (role, message) VALUES (%s, %s)",
        (role, message)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_chat_history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role, message FROM interview_logs ORDER BY id ASC")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs



def create_feedback_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 피드백 결과를 저장할 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_title VARCHAR(100),
            overall_score INT,
            good_points TEXT,
            bad_points TEXT,
            improvement_tips TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_feedback(job_title, score, good, bad, tips):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO interview_feedback (job_title, overall_score, good_points, bad_points, improvement_tips)
        VALUES (%s, %s, %s, %s, %s)
    """, (job_title, score, good, bad, tips))
    conn.commit()
    cursor.close()
    conn.close()

def get_latest_feedback():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM interview_feedback ORDER BY id DESC LIMIT 1")
    feedback = cursor.fetchone()
    cursor.close()
    conn.close()
    return feedback