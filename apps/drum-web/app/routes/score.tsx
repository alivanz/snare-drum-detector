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
		<div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
			<div className="max-w-lg mx-auto text-center">
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">Game Over!</h1>
					<div className="flat-card p-6 mb-6">
						<div className="text-6xl mb-4">🎉</div>
						<h2 className="text-3xl font-bold text-green-400 mb-2">
							Final Score
						</h2>
						<div className="text-5xl font-mono text-white mb-4">247</div>
						<p className="text-zinc-400">hits in 30 seconds</p>
						<div className="mt-4 p-3 bg-zinc-800 border border-zinc-700">
							<div className="text-sm text-zinc-300">
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

				<div className="flat-card p-6 mb-8">
					<h3 className="text-xl font-semibold text-white mb-4">
						Enter Your Name
					</h3>
					<div className="space-y-4">
						<input
							type="text"
							placeholder="Your name"
							className="w-full flat-input"
							maxLength={20}
						/>
						<button className="w-full flat-button-primary">
							Submit to Leaderboard
						</button>
					</div>
				</div>

				<div className="space-y-4">
					<div className="flex justify-center space-x-4">
						<Link to="/" className="flat-button">
							Play Again
						</Link>
						<Link to="/leaderboard" className="flat-button">
							View Leaderboard
						</Link>
					</div>
				</div>
			</div>
		</div>
	);
}
