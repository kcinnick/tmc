CREATE DATABASE tmc;
USE tmc;
CREATE TABLE `posts` (
	`id` INT NOT NULL UNIQUE,
	`thread_title` VARCHAR(200),
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
ALTER TABLE `posts` ADD `in_reply_to` VARCHAR(200) DEFAULT 'tbd';
