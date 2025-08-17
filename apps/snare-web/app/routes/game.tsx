import { Link } from "react-router";
import type { Route } from "./+types/game";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Game - Snare Drum Challenge" },
		{ name: "description", content: "Hit the snare drum as fast as you can!" },
	];
}

export default function Game() {
	return (
		<div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
			<div className="max-w-4xl mx-auto text-center">
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">
						Snare Drum Challenge
					</h1>
					<div className="flex justify-center items-center space-x-8 text-2xl">
						<div className="bg-gray-800 px-6 py-3 rounded-lg border border-gray-700">
							<span className="text-gray-400">Time:</span>
							<span className="text-red-400 font-mono ml-2">30.0s</span>
						</div>
						<div className="bg-gray-800 px-6 py-3 rounded-lg border border-gray-700">
							<span className="text-gray-400">Score:</span>
							<span className="text-green-400 font-mono ml-2">0</span>
						</div>
					</div>
				</div>

				<div className="mb-8">
					<div className="w-80 h-80 mx-auto bg-gradient-to-br from-red-600 to-red-800 rounded-full border-8 border-red-500 snare-glow flex items-center justify-center cursor-pointer hover:scale-105 transition-transform duration-100">
						<span className="text-8xl">🥁</span>
					</div>
					<p className="text-gray-400 mt-4 text-lg">
						Click the drum to hit it!
					</p>
				</div>

				<div className="space-y-4">
					<div className="text-gray-500 text-lg">
						Ready to start? Click the drum when you're ready!
					</div>

					<div className="flex justify-center space-x-4">
						<Link
							to="/"
							className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
						>
							Back to Home
						</Link>
						<Link
							to="/score"
							className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
						>
							Finish Game
						</Link>
					</div>
				</div>
			</div>

			<div className="fixed bottom-4 right-4 bg-gray-800 p-4 rounded-lg border border-gray-700">
				<div className="text-gray-400 text-sm">
					<div>
						Click Rate: <span className="text-white">0.0 hits/sec</span>
					</div>
					<div>
						Best Combo: <span className="text-yellow-400">0</span>
					</div>
				</div>
			</div>
		</div>
	);
}
