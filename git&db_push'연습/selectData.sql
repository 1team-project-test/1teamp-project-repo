-- 1. [스팸 위험도 분석] 신고 횟수가 높은 순으로 정렬하여 탑 3 스팸 번호 조회
SELECT PHONE_NUM, RP_NUM, COMMENT 
FROM SPAM_TABLE 
WHERE SPAM_ST = 'Y'
ORDER BY RP_NUM DESC 
LIMIT 3;

-- 2. [가입 통계] 연령대별 회원 수와 평균 나이 계산
-- (나이를 10으로 나누고 버림하여 연령대 구하기)
SELECT 
    FLOOR(AGE / 10) * 10 AS 연령대,
    COUNT(*) AS 회원수,
    ROUND(AVG(AGE), 1) AS 평균나이
FROM USER_TABLE
GROUP BY FLOOR(AGE / 10)
ORDER BY 연령대;

-- 3. [최신 로그] 오늘(2026년 6월 8일) 검색된 기록만 최신순으로 조회
SELECT LOG_NUM, USER_ID, PHONE_NUM, SEARCH_DATE 
FROM SEARCH_TABLE 
WHERE SEARCH_DATE >= '2026-06-08 00:00:00'
ORDER BY SEARCH_DATE DESC;

-- 4. [보안 점검] 비밀번호를 안전하지 않게 설정한(나이 또는 아이디를 포함하는 등) 유저 찾기
-- (예시: 임시 비밀번호 'TEMP'를 아직 안 바꾼 유저들 조회)
SELECT USER_ID, `E-mail`, IN_DATE 
FROM USER_TABLE 
WHERE PSW LIKE 'TEMP%';


-- 5. [검색 기록 상세] 누가(이메일), 언제(날짜), 어떤 번호(폰번호)를 검색했는지 결합 조회
SELECT 
    S.LOG_NUM,
    U.`E-mail` AS 검색한_유저_이메일,
    S.PHONE_NUM AS 검색한_번호,
    S.SEARCH_DATE
FROM SEARCH_TABLE S
INNER JOIN USER_TABLE U ON S.USER_ID = U.USER_ID
ORDER BY S.SEARCH_DATE DESC;

-- 6. [위험 알림] 유저들이 검색한 번호 중 '실제 스팸(Y)'으로 등록된 번호와 코멘트 매칭 조회
SELECT 
    S.LOG_NUM,
    S.USER_ID,
    S.PHONE_NUM,
    P.RP_NUM AS 총_신고_횟수,
    P.COMMENT AS 스팸_사유,
    S.SEARCH_DATE
FROM SEARCH_TABLE S
INNER JOIN SPAM_TABLE P ON S.PHONE_NUM = P.PHONE_NUM
WHERE P.SPAM_ST = 'Y'
ORDER BY S.SEARCH_DATE DESC;

-- 7. [부서 간 공유 데이터] 부재중 전화(MISSING='Y') 로그 중 스팸 번호였던 내역만 필터링
SELECT 
    S.LOG_NUM,
    S.USER_ID,
    S.PHONE_NUM,
    P.COMMENT
FROM SEARCH_TABLE S
INNER JOIN SPAM_TABLE P ON S.PHONE_NUM = P.PHONE_NUM
WHERE S.MISSING = 'Y' AND P.SPAM_ST = 'Y';

-- 8. [미등록 번호 추출] 검색은 되었으나 아직 스팸 테이블(SPAM_TABLE)에 등록되지 않은 '클린/신종' 번호 찾기
SELECT DISTINCT S.PHONE_NUM 
FROM SEARCH_TABLE S
LEFT JOIN SPAM_TABLE P ON S.PHONE_NUM = P.PHONE_NUM
WHERE P.PHONE_NUM IS NULL;


-- 9. [헤비 유저 발견] 전체 평균 검색 횟수보다 더 많이 검색을 이용한 '열혈 이용자'의 아이디와 이메일 조회
SELECT USER_ID, `E-mail`
FROM USER_TABLE
WHERE USER_ID IN (
    SELECT USER_ID 
    FROM SEARCH_TABLE 
    GROUP BY USER_ID 
    HAVING COUNT(*) > (SELECT COUNT(*) / COUNT(DISTINCT USER_ID) FROM SEARCH_TABLE)
);

-- 10. [스팸 기여도] 가장 많은 스팸 번호를 검색하여 잡아낸 유저 top 1의 아이디와 검색 횟수
SELECT USER_ID, COUNT(*) AS 스팸_검색_건수
FROM SEARCH_TABLE
WHERE PHONE_NUM IN (SELECT PHONE_NUM FROM SPAM_TABLE WHERE SPAM_ST = 'Y')
GROUP BY USER_ID
ORDER BY 스팸_검색_건수 DESC
LIMIT 1;