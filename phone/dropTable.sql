-- 1. 검색 로그 테이블 삭제 (가장 먼저 삭제해야 함)
DROP TABLE SEARCH_TABLE;

-- 2. 스팸 번호 테이블 삭제
DROP TABLE SPAM_TABLE;

-- 3. 유저 테이블 삭제
DROP TABLE USER_TABLE;

-- 4. [안전한 삭제] 테이블이 존재할 때만 삭제 (에러 방지용으로 권장)
DROP TABLE IF EXISTS SEARCH_TABLE;
DROP TABLE IF EXISTS SPAM_TABLE;
DROP TABLE IF EXISTS USER_TABLE;