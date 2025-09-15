import { Link, Outlet, useLocation } from "react-router";

export default function Layout() {
	const location = useLocation();
	const currentPath = location.pathname;
	
	return (
		<>
			<Outlet />
			
			{/* Small fixed navigation with icons */}
			<nav className="fixed bottom-4 left-4 flex gap-2 bg-black/20 backdrop-blur-sm rounded-full px-3 py-2">
				<Link
					to="/"
					className={`text-2xl transition-all ${
						currentPath === "/" ? "text-white/80" : "text-white/30 hover:text-white/60"
					}`}
					title="Home"
				>
					🏠
				</Link>
				
				<Link
					to="/leaderboard"
					className={`text-2xl transition-all ${
						currentPath === "/leaderboard" ? "text-white/80" : "text-white/30 hover:text-white/60"
					}`}
					title="Leaderboard"
				>
					🏆
				</Link>
				
				<Link
					to="/settings"
					className={`text-2xl transition-all ${
						currentPath === "/settings" ? "text-white/80" : "text-white/30 hover:text-white/60"
					}`}
					title="Settings"
				>
					⚙️
				</Link>
				
				<Link
					to="/locations"
					className={`text-2xl transition-all ${
						currentPath === "/locations" ? "text-white/80" : "text-white/30 hover:text-white/60"
					}`}
					title="Locations"
				>
					📍
				</Link>
			</nav>
		</>
	);
}
