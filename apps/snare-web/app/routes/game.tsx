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
		<div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4">
			<div className="max-w-4xl mx-auto text-center">
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">
						Snare Drum Challenge
					</h1>
					<div className="flex justify-center items-center space-x-8 text-2xl">
						<div className="flat-card px-6 py-3">
							<span className="text-zinc-400">Time:</span>
							<span className="text-red-400 font-mono ml-2">30.0s</span>
						</div>
						<div className="flat-card px-6 py-3">
							<span className="text-zinc-400">Score:</span>
							<span className="text-green-400 font-mono ml-2">0</span>
						</div>
					</div>
				</div>

				<div className="mb-12">
					<div className="w-80 h-80 mx-auto bg-red-600 border-4 border-red-500 flex items-center justify-center">
						<span className="text-8xl">🥁</span>
					</div>
				</div>

				<div className="mb-8 flat-card p-8">
					<div className="text-6xl font-bold text-red-400 mb-4">3</div>
					<div className="text-xl text-zinc-300">Get ready...</div>
					<div className="text-sm text-zinc-500 mt-2">
						Game starts in 3 seconds. Prepare your drumsticks!
					</div>
				</div>

				<div className="space-y-4">
					<div className="text-zinc-400 text-lg">
						Hit your physical snare drum to score points!
					</div>

					<div className="flex justify-center">
						<Link
							to="/"
							className="flat-button"
						>
							Cancel Game
						</Link>
					</div>
				</div>
			</div>

			<div className="fixed bottom-4 right-4 flat-card p-4">
				<div className="text-zinc-400 text-sm">
					<div>
						Hit Rate: <span className="text-white">0.0 hits/sec</span>
					</div>
					<div>
						Best Combo: <span className="text-yellow-400">0</span>
					</div>
				</div>
			</div>
		</div>
	);
}
