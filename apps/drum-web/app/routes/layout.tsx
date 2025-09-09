import { Link } from "react-router";

interface LayoutProps {
	children: React.ReactNode;
	currentPage?: "home" | "leaderboard" | "settings";
}

export function Layout({ children, currentPage }: LayoutProps) {
	return (
		<div className="min-h-screen bg-zinc-950 flex">
			<main className="flex-1 p-8 overflow-y-auto">{children}</main>

			<aside className="w-80 bg-zinc-900 border-l border-zinc-800 flex flex-col sticky top-0 h-screen">
				<div className="flex-1">
					<nav>
						<Link
							to="/"
							className={`block w-full text-left flat-button ${
								currentPage === "home"
									? "bg-zinc-700 text-white"
									: "hover:bg-zinc-700"
							}`}
						>
							How to Play
						</Link>

						<Link
							to="/leaderboard"
							className={`block w-full text-left flat-button ${
								currentPage === "leaderboard"
									? "bg-zinc-700 text-white"
									: "hover:bg-zinc-700"
							}`}
						>
							🏆 Leaderboard
						</Link>

						<Link
							to="/settings"
							className={`block w-full text-left flat-button ${
								currentPage === "settings"
									? "bg-zinc-700 text-white"
									: "hover:bg-zinc-700"
							}`}
						>
							⚙️ Settings
						</Link>
					</nav>
				</div>

				<div className="border-t border-zinc-800">
					<Link
						to="/game"
						className="block w-full text-center flat-button-primary text-xl font-bold py-6"
					>
						START CHALLENGE
					</Link>
				</div>
			</aside>
		</div>
	);
}