CREATE DATABASE tmc;
USE tmc;
DROP TABLE posts;
CREATE TABLE `posts` (
	`id` INT NOT NULL UNIQUE,
	`thread_title` VARCHAR(200),
	`username` VARCHAR(90) NOT NULL,
	`posted_at` TEXT NOT NULL,
	`message` TEXT,
	`media` TEXT,
	`likes` INT,
	`loves` INT,
	`helpful` INT,
	`sentiment` INT,
	PRIMARY KEY (`id`)
);
ALTER TABLE `posts` ADD `in_reply_to` VARCHAR(200) DEFAULT 'tbd';
