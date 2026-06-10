-- 1. 기존에 같은 이름의 계정이 있다면 삭제합니다.
DROP USER IF EXISTS '1team'@'localhost';

-- 2. '1team'라는 계정을 만들고 비밀번호를 'tiger'로 설정합니다.
CREATE USER '1team'@'localhost' IDENTIFIED BY 'tiger';

-- 3. [중요] 데이터를 담을 데이터베이스(스키마)를 먼저 생성해야 합니다 (주석 해제).
CREATE DATABASE 1team_schema;

-- 4. 방금 만든 데이터베이스에 대한 모든 권한을 '1team' 계정에 부여합니다.
GRANT ALL PRIVILEGES ON 1team_schema.* TO '1team'@'localhost';

-- 5. 변경된 권한 설정을 즉시 적용합니다.
FLUSH PRIVILEGES;

-- 6. 콘솔을 종료합니다.
EXIT;