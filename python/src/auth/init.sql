CREATE USER 'auth_user'@'localhost' IDENTIFIED BY 'auth123';

CrEATE DATABASE auth;

GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';

USE auth;

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

INSERT INTO user (email, password_hash) VALUES ('durvesh@gmail.com', 'pass123');