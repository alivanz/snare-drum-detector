import { Link, redirect, useLoaderData } from "react-router";
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

export async function loader({ context }: Route.LoaderArgs) {
	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	// Get current settings
	const currentSettings = await stub.getSettings();

	// If no settings is set, redirect to settings
	if (!currentSettings) {
		return redirect("/settings");
	}

	// Get the highest score for the current location and game duration
	const maxScore = await stub.getHighestScore({
		locationId: currentSettings.locationId,
		gameDuration: currentSettings.gameDuration
	});

	return {
		maxScore,
		locationId: currentSettings.locationId,
		gameDuration: currentSettings.gameDuration,
	};
}

export default function Home() {
	const { maxScore, gameDuration } = useLoaderData<typeof loader>();

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
			{/* All Time Record Display */}
			<div className="bg-neutral-800 rounded-lg px-48 py-12 border-4 border-white mb-16">
				<h1 className="text-2xl text-white uppercase tracking-widest mb-2 text-center">
					ALL TIME RECORD
				</h1>
				<p className="text-sm text-white/60 uppercase tracking-wider mb-6 text-center">
					{gameDuration}s Challenge
				</p>
				<div className="text-9xl font-bold text-white text-center">
					{maxScore !== null ? maxScore.toLocaleString() : "---"}
				</div>
			</div>

			{/* Start Challenge Button */}
			<Link
				to="/game"
				className="hover:scale-105 transition-transform"
			>
				<img 
					src="/energi-besar.svg"
					alt="START CHALLENGE"
					className="h-20"
				/>
			</Link>
		</div>
	);
}
