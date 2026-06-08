DELETE FROM SEARCH_TABLE;
DELETE FROM SPAM_TABLE;
DELETE FROM USER_TABLE;

INSERT INTO USER_TABLE (USER_ID, `E-mail`, PSW, IN_DATE, AGE) VALUES 
('user01', 'kim123@gmail.com', '001user', '2026-01-15 10:20:00', 25),
('user02', 'lee_star@naver.com', '002user', '2026-02-20 14:35:12', 34),
('user03', 'park_cyber@daum.net', '003user', '2026-03-05 09:00:45', 41),
('user04', 'choi_99@gmail.com', '004user', '2026-03-12 18:22:19', 28),
('user05', 'jung_secure@outlook.com', '005user', '2026-04-01 11:15:30', 52),
('user06', 'kang_dev@gmail.com', '006user', '2026-04-18 23:50:00', 31),
('user07', 'yoon_biz@naver.com', '007user', '2026-05-02 13:10:22', 45),
('user08', 'jang_student@daum.net', '008user', '2026-05-20 16:40:05', 21);


INSERT INTO SPAM_TABLE (PHONE_NUM, SPAM_ST, RP_NUM, COMMENT) VALUES 
('010-1234-5678', 'Y', 15, '보이스피싱 - 검찰 사칭 유도 번호'),
('02-987-6543', 'Y', 42, '주식 리딩방 가입 권유 자동 음성 메세지'),
('010-5555-4444', 'N', 1, '오인 신고 의심 - 정상 개인 번호'),
('010-8888-9999', 'Y', 8, '대출 권유 및 불법 도박 사이트 홍보'),
('070-1111-2222', 'Y', 124, '인터넷 가입 및 결합 상품 권유 스팸'),
('010-3333-7777', 'N', 0, '최초 등록 번호 - 스팸 의심 검토 중'),
('010-1234-4321', 'Y', 13, '대출 권유');



INSERT INTO SEARCH_TABLE (LOG_NUM, PHONE_NUM, USER_ID, MISSING, SEARCH_DATE) VALUES 
(1001, '010-1234-5678', 'user01', 'N', '2026-06-01 09:30:00'),
(1002, '02-987-6543', 'user01', 'Y', '2026-06-02 11:15:22'),
(1003, '010-5555-4444', 'user02', 'N', '2026-06-03 14:05:40'),
(1004, '010-8888-9999', 'user04', 'N', '2026-06-05 17:22:11'),
(1005, '070-1111-2222', 'user06', 'Y', '2026-06-07 21:45:00'),
(1006, '010-1234-5678', 'user03', 'N', '2026-06-08 08:12:35');