import { DurableObject } from "cloudflare:workers";
import { type AnyColumn, desc, eq, sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/durable-sqlite";
import { migrate } from "drizzle-orm/durable-sqlite/migrator";
import migrations from "./migrations/migrations.js";
import {
	type Location,
	locations,
	type NewLocation,
	type NewScore,
	type Score,
	type Settings,
	scores,
	settings,
} from "./schema";

// Helper function for excluded columns in upsert
const excluded = (column: AnyColumn) => sql.raw(`excluded.${column.name}`);

export class ScoreStorage extends DurableObject<Env> {
	private db: ReturnType<typeof drizzle>;

	constructor(ctx: DurableObjectState, env: Env) {
		super(ctx, env);
		this.db = drizzle(ctx.storage);

		// Run migrations on initialization
		ctx.blockConcurrencyWhile(async () => {
			await migrate(this.db, migrations);
		});
	}

	async addScore(
		scoreData: Omit<NewScore, "id" | "timestamp">,
	): Promise<Score> {
		const [insertedScore] = await this.db
			.insert(scores)
			.values(scoreData)
			.returning();

		return insertedScore;
	}

	async addLocation(locationData: NewLocation): Promise<Location> {
		const [insertedLocation] = await this.db
			.insert(locations)
			.values(locationData)
			.returning();

		return insertedLocation;
	}

	async getLocations(): Promise<Location[]> {
		return await this.db.select().from(locations);
	}

	async getScoresByLocation(locationId: string): Promise<Score[]> {
		return await this.db
			.select()
			.from(scores)
			.where(eq(scores.locationId, locationId))
			.orderBy(desc(scores.score));
	}

	async getHighestScore(locationId: string): Promise<number | null> {
		const result = await this.db
			.select({ maxScore: sql<number>`MAX(${scores.score})` })
			.from(scores)
			.where(eq(scores.locationId, locationId));
		
		return result[0]?.maxScore ?? null;
	}

	async getSettings(): Promise<Settings | null> {
		const [result] = await this.db
			.select()
			.from(settings)
			.where(eq(settings.id, "default"));

		return result || null;
	}

	async getSettingsWithLocation(): Promise<{ settings: Settings; location: Location } | null> {
		const [result] = await this.db
			.select({
				settings: settings,
				location: locations,
			})
			.from(settings)
			.innerJoin(locations, eq(settings.locationId, locations.id))
			.where(eq(settings.id, "default"));

		return result || null;
	}

	async updateSettings(locationId: string): Promise<Settings> {
		// Use upsert (insert with onConflictDoUpdate) with excluded helper
		const [upserted] = await this.db
			.insert(settings)
			.values({
				id: "default",
				locationId,
				updatedAt: new Date(),
			})
			.onConflictDoUpdate({
				target: settings.id,
				set: {
					locationId: excluded(settings.locationId),
					updatedAt: excluded(settings.updatedAt),
				},
			})
			.returning();

		return upserted;
	}
}
