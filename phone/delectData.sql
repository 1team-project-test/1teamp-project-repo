-- 1. 특정 검색 로그 하나만 삭제 (가장 안전한 기본 PK 삭제)
DELETE FROM SEARCH_TABLE 
WHERE LOG_NUM = 1001;

-- 2. 특정 유저('user01')가 검색한 모든 로그 기록 지우기
DELETE FROM SEARCH_TABLE 
WHERE USER_ID = 'user01';

-- 3. 오래된 로그 정리 (2026년 1월 1일 이전의 모든 검색 기록 삭제)
DELETE FROM SEARCH_TABLE 
WHERE SEARCH_DATE < '2026-01-01 00:00:00';

-- 4. 부재중 전화가 아니고('N'), 최근 스팸 번호도 아닌 검색 기록 삭제
DELETE FROM SEARCH_TABLE 
WHERE MISSING = 'N' AND PHONE_NUM NOT IN (SELECT PHONE_NUM FROM SPAM_TABLE WHERE SPAM_ST = 'Y');

-- 5. 오인 신고로 밝혀져 신고 횟수(RP_NUM)가 0인 정상 번호 목록 스팸 테이블에서 지우기
DELETE FROM SPAM_TABLE 
WHERE RP_NUM = 0 AND SPAM_ST = 'N';

-- 6. 특정 회원 탈퇴 처리하기
-- [단계 1] 자식 테이블(SEARCH_TABLE)에서 'user03'의 검색 로그를 먼저 삭제
DELETE FROM SEARCH_TABLE 
WHERE USER_ID = 'user03';

DELETE FROM USER_TABLE 
WHERE USER_ID = 'user03';

-- 7. [전체 삭제] SEARCH_TABLE의 모든 데이터 초기화 (테이블 구조는 남음)
-- DELETE FROM SEARCH_TABLE;
