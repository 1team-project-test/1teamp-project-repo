-- 1. 특정 유저('user01')의 비밀번호 변경
UPDATE USER_TABLE 
SET PSW = '123456' 
WHERE USER_ID = 'user01';

-- 2. 특정 유저('user02')가 이메일을 변경하고 한 살 더 먹었을 때 (여러 컬럼 동시 수정)
UPDATE USER_TABLE 
SET `E-mail` = 'lee_new@naver.com', AGE = 35 
WHERE USER_ID = 'user02';

-- 3. 올해 새해가 되어 모든 유저의 나이를 일괄적으로 1살씩 증가시킬 때 (조건 없음)
UPDATE USER_TABLE 
SET AGE = AGE + 1;

-- 4. 가입일(IN_DATE)이 누락된 유저가 있다면 현재 시간으로 채워넣기
UPDATE USER_TABLE 
SET IN_DATE = NOW() 
WHERE IN_DATE IS NULL;

-- 5. 나이가 20세 미만인 유저들의 비밀번호를 임시 비밀번호로 강제 초기화
UPDATE USER_TABLE 
SET PSW = 'TEMPPWD123!' 
WHERE AGE < 20;

-- 6. 특정 번호('010-1234-5678')에 대한 스팸 신고가 추가로 들어와 신고 횟수(RP_NUM)를 1 증가
UPDATE SPAM_TABLE 
SET RP_NUM = RP_NUM + 1 
WHERE PHONE_NUM = '010-1234-5678';

-- 7. 누적 신고 횟수(RP_NUM)가 50회가 넘은 번호는 자동으로 스팸 상태를 'Y'로 변경
UPDATE SPAM_TABLE 
SET SPAM_ST = 'Y' 
WHERE RP_NUM >= 50;

-- 8. 스팸 번호의 코멘트 내용 수정 및 스팸 상태 변경
UPDATE SPAM_TABLE 
SET COMMENT = '[강력의심] 주식 사기 유도 번호', SPAM_ST = 'Y' 
WHERE PHONE_NUM = '02-987-6543';

-- 9. 오인 신고로 판명된 번호의 신고 횟수를 0으로 초기화하고 정상 번호('N')로 처리
UPDATE SPAM_TABLE 
SET RP_NUM = 0, SPAM_ST = 'N', COMMENT = '확인 결과 정상 번호로 판명됨' 
WHERE PHONE_NUM = '010-5555-4444';

-- 10. 코멘트가 비어 있는(NULL 또는 공백) 스팸 번호들에 일괄적으로 기본 문구 넣기
UPDATE SPAM_TABLE 
SET COMMENT = '상세 정보 없음' 
WHERE COMMENT IS NULL OR COMMENT = '';


-- 11. 특정 검색 로그(LOG_NUM = 1001)의 미수신 여부(MISSING)를 'Y'로 변경
UPDATE SEARCH_TABLE 
SET MISSING = 'Y' 
WHERE LOG_NUM = 1001;

-- 12. 특정 유저('USR001')가 검색했던 모든 기록의 검색 날짜를 현재 시간으로 최신화
UPDATE SEARCH_TABLE 
SET SEARCH_DATE = NOW() 
WHERE USER_ID = 'user01';

-- 13. 잘못 입력된 전화번호 로그 수정 (오타 수정)
UPDATE SEARCH_TABLE 
SET PHONE_NUM = '010-8888-9999' 
WHERE LOG_NUM = 1004;

-- 14. 특정 날짜('2026-06-01') 이전에 검색된 모든 기록의 미수신 상태를 'N'으로 일괄 변경
UPDATE SEARCH_TABLE 
SET MISSING = 'N' 
WHERE SEARCH_DATE < '2026-06-01 00:00:00';

