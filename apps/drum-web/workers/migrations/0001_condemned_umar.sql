ALTER TABLE `scores` ADD `game_duration` integer DEFAULT 60 NOT NULL;--> statement-breakpoint
ALTER TABLE `settings` ADD `game_duration` integer DEFAULT 30 NOT NULL;