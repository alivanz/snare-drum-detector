import { useState } from "react";
import { Link } from "react-router";
import type { Route } from "./+types/settings";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Settings - Snare Drum Challenge" },
		{
			name: "description",
			content: "Select your city to compete on local leaderboards!",
		},
	];
}

const indonesianCities = [
	{ id: "jakarta", name: "Jakarta" },
	{ id: "surabaya", name: "Surabaya" },
	{ id: "bandung", name: "Bandung" },
	{ id: "medan", name: "Medan" },
	{ id: "semarang", name: "Semarang" },
	{ id: "makassar", name: "Makassar" },
	{ id: "palembang", name: "Palembang" },
	{ id: "tangerang", name: "Tangerang" },
	{ id: "depok", name: "Depok" },
	{ id: "bekasi", name: "Bekasi" },
	{ id: "batam", name: "Batam" },
	{ id: "yogyakarta", name: "Yogyakarta" },
];

export default function Settings() {
	const [selectedCity, setSelectedCity] = useState("");

	const handleSave = () => {
		// TODO: Save to Durable Object
		console.log("Saving city:", selectedCity);
	};

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
			{/* Settings Card */}
			<div className="bg-black/60 backdrop-blur-sm rounded-lg p-12 border-2 border-white/30 min-w-[500px]">
				<h1 className="text-3xl text-white uppercase tracking-widest mb-8 text-center font-bold">
					SETTINGS
				</h1>
				
				<div className="mb-8">
					<label className="block text-white/80 uppercase tracking-wider text-sm mb-4">
						SELECT YOUR CITY
					</label>
					<select 
						value={selectedCity}
						onChange={(e) => setSelectedCity(e.target.value)}
						className="w-full px-4 py-3 bg-black/50 border border-white/30 text-white rounded focus:outline-none focus:border-white/60"
					>
						<option value="">Choose a city...</option>
						{indonesianCities.map((city) => (
							<option key={city.id} value={city.id}>
								{city.name}
							</option>
						))}
					</select>
				</div>

				{/* Save Button */}
				<button
					onClick={handleSave}
					disabled={!selectedCity}
					className="w-full px-6 py-4 rounded-lg font-bold text-2xl uppercase tracking-wider transition-all"
					style={{
						background: selectedCity 
							? "linear-gradient(180deg, #E0E0E0 0%, #9E9E9E 50%, #757575 100%)"
							: "linear-gradient(180deg, #606060 0%, #404040 50%, #303030 100%)",
						boxShadow: "0 4px 8px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)",
						color: selectedCity ? "black" : "#666",
						cursor: selectedCity ? "pointer" : "not-allowed",
					}}
				>
					Save
				</button>
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
