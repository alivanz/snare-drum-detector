import { Link } from "react-router";
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

const mockLeaderboards = {
	jakarta: [
		{ rank: 1, name: "JakartaDrummer", score: 342, date: "2024-08-15" },
		{ rank: 2, name: "CapitalBeats", score: 328, date: "2024-08-14" },
		{ rank: 3, name: "MetroRhythm", score: 315, date: "2024-08-16" },
		{ rank: 4, name: "CitySnare", score: 298, date: "2024-08-13" },
		{ rank: 5, name: "JKTMaster", score: 284, date: "2024-08-15" },
		{ rank: 6, name: "TowerBeats", score: 271, date: "2024-08-12" },
		{ rank: 7, name: "MegaHits", score: 267, date: "2024-08-17" },
		{ rank: 8, name: "UrbanDrum", score: 255, date: "2024-08-11" },
		{ rank: 9, name: "JKTRhythm", score: 248, date: "2024-08-16" },
		{ rank: 10, name: "CapitalHits", score: 241, date: "2024-08-10" },
	],
	surabaya: [
		{ rank: 1, name: "SurabayaStick", score: 334, date: "2024-08-15" },
		{ rank: 2, name: "EastJavaBeats", score: 321, date: "2024-08-14" },
		{ rank: 3, name: "SBYDrummer", score: 308, date: "2024-08-16" },
		{ rank: 4, name: "HeroesHits", score: 295, date: "2024-08-13" },
		{ rank: 5, name: "PortRhythm", score: 282, date: "2024-08-15" },
		{ rank: 6, name: "SuraBeats", score: 269, date: "2024-08-12" },
		{ rank: 7, name: "EastPower", score: 256, date: "2024-08-17" },
		{ rank: 8, name: "BayaHits", score: 243, date: "2024-08-11" },
		{ rank: 9, name: "SBYMaster", score: 230, date: "2024-08-16" },
		{ rank: 10, name: "HeroSnare", score: 225, date: "2024-08-10" },
	],
	bandung: [
		{ rank: 1, name: "BandungBeats", score: 329, date: "2024-08-15" },
		{ rank: 2, name: "ParisVanJava", score: 316, date: "2024-08-14" },
		{ rank: 3, name: "MountainHits", score: 303, date: "2024-08-16" },
		{ rank: 4, name: "BDGDrummer", score: 290, date: "2024-08-13" },
		{ rank: 5, name: "CoolCity", score: 277, date: "2024-08-15" },
		{ rank: 6, name: "WestJavaBeats", score: 264, date: "2024-08-12" },
		{ rank: 7, name: "BandungStick", score: 251, date: "2024-08-17" },
		{ rank: 8, name: "FlowerSnare", score: 238, date: "2024-08-11" },
		{ rank: 9, name: "BDGRhythm", score: 225, date: "2024-08-16" },
		{ rank: 10, name: "ParisHits", score: 220, date: "2024-08-10" },
	],
};

export default function Leaderboard() {
	const currentCity = "jakarta";
	const currentLeaderboard = mockLeaderboards[currentCity] || mockLeaderboards.jakarta;
	const cityNames = {
		jakarta: "Jakarta",
		surabaya: "Surabaya", 
		bandung: "Bandung"
	};

	return (
		<div className="min-h-screen bg-gray-900 p-4">
			<div className="max-w-4xl mx-auto">
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">
						🏆 Hall of Fame
					</h1>
					<p className="text-xl text-gray-300">
						Top 10 Snare Drum Challenge Champions
					</p>
				</div>


				<div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden mb-8">
					<div className="bg-gray-700 px-6 py-4 border-b border-gray-600">
						<h2 className="text-xl font-semibold text-white">
							Leaderboard
						</h2>
					</div>

					<div className="overflow-x-auto">
						<table className="w-full">
							<thead className="bg-gray-750 sticky top-0 z-10">
								<tr className="text-gray-300 text-sm">
									<th className="text-left py-3 px-6 font-semibold">Rank</th>
									<th className="text-left py-3 px-6 font-semibold">Player</th>
									<th className="text-center py-3 px-6 font-semibold">Score</th>
									<th className="text-center py-3 px-6 font-semibold">Date</th>
								</tr>
							</thead>
							<tbody>
								{currentLeaderboard.map((entry, index) => (
									<tr
										key={entry.rank}
										className={`border-b border-gray-700 hover:bg-gray-750 transition-colors ${
											index < 3 ? "bg-gray-750" : ""
										}`}
									>
										<td className="py-4 px-6">
											<div className="flex items-center">
												<span
													className={`text-2xl mr-3 ${
														entry.rank === 1
															? "text-yellow-400"
															: entry.rank === 2
																? "text-gray-400"
																: entry.rank === 3
																	? "text-orange-600"
																	: ""
													}`}
												>
													{entry.rank === 1
														? "🥇"
														: entry.rank === 2
															? "🥈"
															: entry.rank === 3
																? "🥉"
																: ""}
												</span>
												<span
													className={`font-bold ${
														entry.rank <= 3 ? "text-white" : "text-gray-300"
													}`}
												>
													#{entry.rank}
												</span>
											</div>
										</td>
										<td
											className={`py-4 px-6 font-semibold ${
												entry.rank <= 3 ? "text-white" : "text-gray-300"
											}`}
										>
											{entry.name}
										</td>
										<td
											className={`py-4 px-6 text-center font-mono text-lg ${
												entry.rank === 1
													? "text-yellow-400"
													: entry.rank === 2
														? "text-gray-300"
														: entry.rank === 3
															? "text-orange-600"
															: "text-green-400"
											}`}
										>
											{entry.score}
										</td>
										<td className="py-4 px-6 text-center text-gray-400 text-sm">
											{entry.date}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>

				<div className="text-center space-y-4">
					<div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
						<h3 className="text-lg font-semibold text-white mb-2">
							Think you can make it to the top?
						</h3>
						<p className="text-gray-400 mb-4">
							Challenge yourself and climb the leaderboard!
						</p>
						<Link
							to="/"
							className="inline-block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
						>
							Start New Challenge
						</Link>
					</div>

					<div className="flex justify-center">
						<Link to="/" className="text-gray-400 hover:text-white underline">
							← Back to Home
						</Link>
					</div>
				</div>
			</div>
		</div>
	);
}
