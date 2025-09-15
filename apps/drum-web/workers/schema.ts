import { sql } from "drizzle-orm";
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";
import { v7 as uuidv7 } from "uuid";

export const locations = sqliteTable("locations", {
	id: text("id").primaryKey(), // slug like "new-york", "san-francisco"
	name: text("name").notNull(), // display name like "New York", "San Francisco"
});

export const scores = sqliteTable("scores", {
	id: text("id")
		.primaryKey()
		.$defaultFn(() => uuidv7()),
	timestamp: integer("timestamp", { mode: "timestamp" })
		.notNull()
		.default(sql`(unixepoch())`),
	locationId: text("location_id")
		.notNull()
		.references(() => locations.id),
	score: integer("score").notNull(),
	combo: integer("combo").notNull(),
	duration: integer("duration").notNull(), // in milliseconds
});

export type Location = typeof locations.$inferSelect;
export type NewLocation = typeof locations.$inferInsert;
export type Score = typeof scores.$inferSelect;
export type NewScore = typeof scores.$inferInsert;
