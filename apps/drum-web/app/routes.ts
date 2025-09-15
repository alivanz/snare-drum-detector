import type { RouteConfig } from "@react-router/dev/routes";
import { index, layout, route } from "@react-router/dev/routes";

export default [
	layout("routes/layout.tsx", [
		index("routes/home.tsx"),
		route("/leaderboard", "routes/leaderboard.tsx"),
		route("/settings", "routes/settings.tsx"),
		route("/locations", "routes/locations.tsx"),
	]),
	route("/game", "routes/game.tsx"),
	route("/score", "routes/score.tsx"),
] satisfies RouteConfig;
