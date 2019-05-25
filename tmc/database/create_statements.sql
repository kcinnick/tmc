CREATE DATABASE tmc;
USE tmc;
CREATE TABLE `posts` (
	`id` INT NOT NULL UNIQUE,
	`username` VARCHAR(90) NOT NULL,
	`posted_at` DATETIME NOT NULL,
	`message` TEXT,
	`media` TEXT,
	`likes` INT,
	`loves` INT,
	`helpful` INT,
	`sentiment` INT,
	PRIMARY KEY (`id`)
);
