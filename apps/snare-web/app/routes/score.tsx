import { Link } from "react-router";
import type { Route } from "./+types/score";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Submit Score - Snare Drum Challenge" },
		{ name: "description", content: "Enter your name for the leaderboard!" },
	];
}

export default function Score() {
	return (
		<div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
			<div className="max-w-lg mx-auto text-center">
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">Game Over!</h1>
					<div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
						<div className="text-6xl mb-4">🎉</div>
						<h2 className="text-3xl font-bold text-green-400 mb-2">
							Final Score
						</h2>
						<div className="text-5xl font-mono text-white mb-4">247</div>
						<p className="text-gray-400">hits in 30 seconds</p>
						<div className="mt-4 p-3 bg-gray-700 rounded-lg">
							<div className="text-sm text-gray-300">
								<div>
									Average: <span className="text-yellow-400">8.2 hits/sec</span>
								</div>
								<div>
									Best Combo: <span className="text-orange-400">15 hits</span>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
					<h3 className="text-xl font-semibold text-white mb-4">
						Enter Your Name
					</h3>
					<div className="space-y-4">
						<input
							type="text"
							placeholder="Your name"
							className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
							maxLength={20}
						/>
						<button className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200">
							Submit to Leaderboard
						</button>
					</div>
				</div>

				<div className="space-y-4">
					<div className="flex justify-center space-x-4">
						<Link
							to="/"
							className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
						>
							Play Again
						</Link>
						<Link
							to="/leaderboard"
							className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
						>
							View Leaderboard
						</Link>
					</div>
				</div>

				<div className="mt-8 text-gray-500 text-sm">
					<p>Think you can do better? Challenge your friends!</p>
				</div>
			</div>
		</div>
	);
}
