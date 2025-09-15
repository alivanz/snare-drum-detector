import type { Route } from "./+types/settings";
import { Layout } from "./layout";

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
		<Layout currentPage="settings">
			<div className="max-w-2xl mx-auto">
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">⚙️ Settings</h1>
					<p className="text-xl text-zinc-300">
						Select your city to compete on the local leaderboard
					</p>
				</div>

				<div className="flat-card p-8 mb-8">
					<div className="mb-6">
						<h2 className="text-2xl font-semibold text-white mb-4">
							🏙️ Select Your City
						</h2>
						<p className="text-zinc-400 mb-6">
							Choose your city to compete with players in your area. Each city
							has its own leaderboard!
						</p>
					</div>

					<div className="space-y-4">
						<label className="block text-sm font-medium text-zinc-300 mb-2">
							City *
						</label>
						<select className="w-full flat-input">
							<option value="">Select your city...</option>
							{indonesianCities.map((city) => (
								<option key={city.id} value={city.id}>
									{city.name}, {city.province}
								</option>
							))}
						</select>
						<p className="text-sm text-zinc-500">
							Don't see your city? We're constantly adding new locations!
						</p>
					</div>

					<div className="mt-8 p-4 bg-zinc-800 border border-zinc-700">
						<h3 className="text-lg font-semibold text-white mb-2">
							Current Selection
						</h3>
						<div className="text-zinc-400">
							<span className="text-yellow-400">⚠️ No city selected</span>
						</div>
						<p className="text-sm text-zinc-500 mt-2">
							You must select a city to participate in leaderboards
						</p>
					</div>
				</div>

				<div className="space-y-4">
					<button className="w-full flat-button-primary">Save Settings</button>
				</div>

				<div className="mt-8 flat-card p-6">
					<h3 className="text-lg font-semibold text-white mb-3">
						🌏 About City Leaderboards
					</h3>
					<ul className="text-zinc-300 space-y-2 text-sm">
						<li>• Each city has its own separate leaderboard</li>
						<li>• Compete with players in your local area</li>
						<li>
							• Your scores will only appear on your selected city's leaderboard
						</li>
						<li>• You can change your city selection anytime</li>
					</ul>
				</div>
			</div>
		</Layout>
	);
}
