import { DurableObject } from "cloudflare:workers";
import { desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/durable-sqlite";
import { migrate } from "drizzle-orm/durable-sqlite/migrator";
import migrations from "./migrations/migrations.js";
import {
	type Location,
	locations,
	type NewLocation,
	type NewScore,
	type Score,
	scores,
} from "./schema";

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
}
