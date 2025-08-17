import { Link } from "react-router";
import type { Route } from "./+types/settings";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Settings - Snare Drum Challenge" },
		{ name: "description", content: "Select your city to compete on local leaderboards!" },
	];
}

const indonesianCities = [
	{ id: "jakarta", name: "Jakarta", province: "DKI Jakarta" },
	{ id: "surabaya", name: "Surabaya", province: "Jawa Timur" },
	{ id: "bandung", name: "Bandung", province: "Jawa Barat" },
	{ id: "medan", name: "Medan", province: "Sumatera Utara" },
	{ id: "semarang", name: "Semarang", province: "Jawa Tengah" },
	{ id: "makassar", name: "Makassar", province: "Sulawesi Selatan" },
	{ id: "palembang", name: "Palembang", province: "Sumatera Selatan" },
	{ id: "tangerang", name: "Tangerang", province: "Banten" },
	{ id: "depok", name: "Depok", province: "Jawa Barat" },
	{ id: "bekasi", name: "Bekasi", province: "Jawa Barat" },
	{ id: "batam", name: "Batam", province: "Kepulauan Riau" },
	{ id: "yogyakarta", name: "Yogyakarta", province: "DI Yogyakarta" },
];

export default function Settings() {
	return (
		<div className="min-h-screen bg-gray-900 p-4">
			<div className="max-w-2xl mx-auto">
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">⚙️ Settings</h1>
					<p className="text-xl text-gray-300">
						Select your city to compete on the local leaderboard
					</p>
				</div>

				<div className="bg-gray-800 rounded-lg p-8 border border-gray-700 mb-8">
					<div className="mb-6">
						<h2 className="text-2xl font-semibold text-white mb-4">
							🏙️ Select Your City
						</h2>
						<p className="text-gray-400 mb-6">
							Choose your city to compete with players in your area. Each city has its own leaderboard!
						</p>
					</div>

					<div className="space-y-4">
						<label className="block text-sm font-medium text-gray-300 mb-2">
							City *
						</label>
						<select className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500">
							<option value="">Select your city...</option>
							{indonesianCities.map((city) => (
								<option key={city.id} value={city.id}>
									{city.name}, {city.province}
								</option>
							))}
						</select>
						<p className="text-sm text-gray-500">
							Don't see your city? We're constantly adding new locations!
						</p>
					</div>

					<div className="mt-8 p-4 bg-gray-700 rounded-lg border border-gray-600">
						<h3 className="text-lg font-semibold text-white mb-2">Current Selection</h3>
						<div className="text-gray-400">
							<span className="text-yellow-400">⚠️ No city selected</span>
						</div>
						<p className="text-sm text-gray-500 mt-2">
							You must select a city to participate in leaderboards
						</p>
					</div>
				</div>

				<div className="space-y-4">
					<button className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200">
						Save Settings
					</button>
					
					<div className="flex justify-center space-x-4">
						<Link
							to="/"
							className="text-gray-400 hover:text-white underline"
						>
							← Back to Home
						</Link>
						<Link
							to="/leaderboard"
							className="text-gray-400 hover:text-white underline"
						>
							View Leaderboard
						</Link>
					</div>
				</div>

				<div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
					<h3 className="text-lg font-semibold text-white mb-3">🌏 About City Leaderboards</h3>
					<ul className="text-gray-300 space-y-2 text-sm">
						<li>• Each city has its own separate leaderboard</li>
						<li>• Compete with players in your local area</li>
						<li>• Your scores will only appear on your selected city's leaderboard</li>
						<li>• You can change your city selection anytime</li>
					</ul>
				</div>
			</div>
		</div>
	);
}