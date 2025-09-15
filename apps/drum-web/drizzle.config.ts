import { defineConfig } from "drizzle-kit";

export default defineConfig({
	schema: "./workers/schema.ts",
	out: "./workers/migrations",
	dialect: "sqlite",
	driver: "durable-sqlite",
});
