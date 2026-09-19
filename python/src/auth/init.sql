-- MYSQL_DATABASE and MYSQL_USER are provisioned by the MySQL container.
USE auth;
CREATE TABLE IF NOT EXISTS user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);
-- Auth seeds a hashed demo password only when DEMO_USER_PASSWORD is set.
