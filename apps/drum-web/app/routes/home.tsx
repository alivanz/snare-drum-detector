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

	// Get the highest score for the current location
	const maxScore = await stub.getHighestScore(currentSettings.locationId);

	return {
		maxScore,
		locationId: currentSettings.locationId,
	};
}

export default function Home() {
	const { maxScore } = useLoaderData<typeof loader>();

	return (
		<div
			className="min-h-screen flex flex-col items-center justify-center p-4"
			style={{
				backgroundImage: "url(/background.jpg)",
				backgroundSize: "cover",
				backgroundPosition: "center",
				backgroundRepeat: "no-repeat",
			}}
		>
			{/* All Time Record Display */}
			<div className="bg-neutral-800 rounded-lg p-12 border-2 border-white/30 mb-16">
				<h1 className="text-2xl text-white/80 uppercase tracking-widest mb-6 text-center">
					ALL TIME RECORD
				</h1>
				<div className="text-8xl font-bold text-white text-center">
					{maxScore !== null ? maxScore.toLocaleString() : "---"}
				</div>
			</div>

			{/* Start Challenge Button */}
			<div
				className="px-16 py-6 rounded-lg cursor-pointer hover:scale-105 transition-transform"
				style={{
					background:
						"linear-gradient(180deg, #E0E0E0 0%, #9E9E9E 50%, #757575 100%)",
					boxShadow:
						"0 6px 12px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.5)",
				}}
			>
				<Link
					to="/game"
					className="text-3xl font-bold text-black uppercase tracking-wider"
				>
					START CHALLENGE
				</Link>
			</div>
		</div>
	);
}
