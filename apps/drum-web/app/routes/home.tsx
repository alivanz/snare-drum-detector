import type { Route } from "./+types/home";
import { Layout } from "./layout";

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
		<Layout currentPage="home">
			<div className="max-w-4xl mx-auto">
				<div className="mb-12">
					<h1 className="text-6xl font-bold text-white mb-4">
						🥁 Snare Drum Challenge
					</h1>
					<p className="text-xl text-zinc-300 mb-8">
						Test your rhythm skills! Hit the snare drum as many times as you can
						in 30 seconds.
					</p>
				</div>

				<div className="flat-card p-8 mb-8">
					<div className="w-48 h-48 mx-auto mb-6 bg-red-600 flex items-center justify-center">
						<span className="text-4xl">🥁</span>
					</div>

					<h2 className="text-2xl font-semibold text-white mb-6">
						How to Play
					</h2>
					<ul className="text-zinc-300 space-y-3 text-left max-w-lg mx-auto text-lg">
						<li>• Click the START button to begin</li>
						<li>• Hit the physical snare drum as fast as you can</li>
						<li>• You have 30 seconds to get the highest score</li>
						<li>• Enter your name for the leaderboard</li>
						<li>• Select your city to compete locally</li>
					</ul>
				</div>

				<div className="flat-card p-6">
					<h3 className="text-xl font-semibold text-white mb-4">Ready to Start?</h3>
					<p className="text-zinc-400">
						Use the START CHALLENGE button in the menu to begin your drum challenge.
						Make sure you've selected your city in Settings first!
					</p>
				</div>
			</div>
		</Layout>
	);
}
