import { Link } from "react-router";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Snare Drum Challenge" },
		{
			name: "description",
			content:
				"Test your rhythm skills in the ultimate snare drum hitting challenge!",
		},
	];
}

export default function Home() {
	return (
		<div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
			<div className="max-w-2xl mx-auto text-center">
				<div className="mb-8">
					<h1 className="text-6xl font-bold text-white mb-4">
						🥁 Snare Drum Challenge
					</h1>
					<p className="text-xl text-gray-300 mb-8">
						Test your rhythm skills! Hit the snare drum as many times as you can
						in 30 seconds.
					</p>
				</div>

				<div className="bg-gray-800 rounded-lg p-8 mb-8 border border-gray-700">
					<div className="w-48 h-48 mx-auto mb-6 bg-gradient-to-br from-red-600 to-red-800 rounded-full border-4 border-red-500 snare-glow flex items-center justify-center">
						<span className="text-4xl">🥁</span>
					</div>

					<h2 className="text-2xl font-semibold text-white mb-4">
						How to Play
					</h2>
					<ul className="text-gray-300 space-y-2 text-left max-w-md mx-auto">
						<li>• Click the START button to begin</li>
						<li>• Hit the snare drum as fast as you can</li>
						<li>• You have 30 seconds to get the highest score</li>
						<li>• Enter your name for the leaderboard</li>
					</ul>
				</div>

				<div className="space-y-4">
					<Link
						to="/game"
						className="inline-block bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-lg text-xl transition-colors duration-200"
					>
						START CHALLENGE
					</Link>

					<div className="flex justify-center space-x-4">
						<Link
							to="/leaderboard"
							className="text-gray-400 hover:text-white underline"
						>
							View Leaderboard
						</Link>
					</div>
				</div>
			</div>
		</div>
	);
}
