import { Link, redirect, useLoaderData } from "react-router";
import type { Route } from "./+types/leaderboard";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Leaderboard - Snare Drum Challenge" },
		{
			name: "description",
			content: "See the top snare drum challenge scores!",
		},
	];
}

export async function loader({ context }: Route.LoaderArgs) {
	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);
	
	// Get current settings with location
	const settingsWithLocation = await stub.getSettingsWithLocation();
	
	// If no location is set, redirect to settings
	if (!settingsWithLocation) {
		return redirect("/settings");
	}
	
	// Get scores for the current location (already sorted by score DESC from the Durable Object)
	const scores = await stub.getScoresByLocation(settingsWithLocation.settings.locationId);
	
	// Add rank to each score
	const rankedScores = scores.map((score, index) => ({
		rank: index + 1,
		score: score.score,
		combo: score.combo,
		duration: score.duration,
		timestamp: score.timestamp,
	}));
	
	return {
		scores: rankedScores,
		locationName: settingsWithLocation.location.name,
	};
}

export default function Leaderboard() {
	const { scores, locationName } = useLoaderData<typeof loader>();

	// Format date and time in a human-readable way
	const formatDateTime = (timestamp: string) => {
		const date = new Date(timestamp);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
		
		// Format time as HH:MM AM/PM
		const timeStr = date.toLocaleTimeString("en-US", {
			hour: "numeric",
			minute: "2-digit",
			hour12: true
		});
		
		// Show relative date for recent scores
		if (diffDays === 0) {
			return `Today at ${timeStr}`;
		} else if (diffDays === 1) {
			return `Yesterday at ${timeStr}`;
		} else if (diffDays < 7) {
			return `${diffDays} days ago at ${timeStr}`;
		} else {
			// Show full date for older scores
			return date.toLocaleDateString("en-US", {
				month: "short",
				day: "numeric",
				year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined
			}) + ` at ${timeStr}`;
		}
	};

	return (
		<div
			className="min-h-screen flex flex-col items-center justify-center p-4"
			style={{
				backgroundImage: "url(/background.png)",
				backgroundSize: "cover",
				backgroundPosition: "center",
				backgroundRepeat: "no-repeat",
			}}
		>
			<div className="bg-black/60 backdrop-blur-sm rounded-lg p-12 border-2 border-white/30 max-w-4xl w-full">
				<h1 className="text-3xl text-white uppercase tracking-widest mb-2 text-center font-bold">
					LEADERBOARD
				</h1>
				<p className="text-xl text-white/60 uppercase tracking-wider mb-8 text-center">
					{locationName}
				</p>

				{scores.length === 0 ? (
					<div className="text-center py-12">
						<p className="text-white/60 text-xl">No scores yet!</p>
						<p className="text-white/40 mt-2">Be the first to set a record!</p>
					</div>
				) : (
					<div className="overflow-x-auto">
						<table className="w-full text-white">
							<thead>
								<tr className="border-b border-white/30">
									<th className="text-left py-3 px-4 uppercase tracking-wider text-sm text-white/80">
										Rank
									</th>
									<th className="text-center py-3 px-4 uppercase tracking-wider text-sm text-white/80">
										Score
									</th>
									<th className="text-center py-3 px-4 uppercase tracking-wider text-sm text-white/80">
										Combo
									</th>
									<th className="text-center py-3 px-4 uppercase tracking-wider text-sm text-white/80">
										When
									</th>
								</tr>
							</thead>
							<tbody>
								{scores.map((entry, index) => (
									<tr
										key={entry.rank}
										className="border-b border-white/10 hover:bg-white/5 transition-colors"
									>
										<td className="py-3 px-4">
											<div className="flex items-center">
												<span className="text-2xl mr-3">
													{entry.rank === 1
														? "🥇"
														: entry.rank === 2
															? "🥈"
															: entry.rank === 3
																? "🥉"
																: ""}
												</span>
												<span className={`font-bold ${
													entry.rank <= 3 ? "text-white" : "text-white/60"
												}`}>
													#{entry.rank}
												</span>
											</div>
										</td>
										<td className={`py-3 px-4 text-center font-mono text-2xl ${
											entry.rank === 1
												? "text-yellow-400"
												: entry.rank === 2
													? "text-gray-300"
													: entry.rank === 3
														? "text-orange-600"
														: "text-white"
										}`}>
											{entry.score.toLocaleString()}
										</td>
										<td className="py-3 px-4 text-center text-white/60">
											{entry.combo}x
										</td>
										<td className="py-3 px-4 text-center text-white/40 text-sm">
											{formatDateTime(entry.timestamp.toString())}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>

			{/* Back to Home */}
			<div className="mt-8">
				<Link 
					to="/" 
					className="text-white text-lg uppercase tracking-wider hover:text-white/80 transition-colors underline"
				>
					Back to Home
				</Link>
			</div>
		</div>
	);
}
